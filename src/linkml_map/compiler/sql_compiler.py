from dataclasses import dataclass

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition

from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SerializationSyntaxType,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.utils.join_utils import join_keys

LINKML_TO_SQL_TYPE_MAP = {
    "string": "TEXT",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
    "float": "REAL",
    "decimal": "REAL",
    "datetime": "TIMESTAMP",
    "date": "DATE",
    "time": "TIME",
    "uri": "TEXT",
    "any": "TEXT",
}

#: Alias bound to the primary (``populated_from``) table in a compiled SELECT.
PRIMARY_ALIAS = "_src"


def _quote(identifier: str) -> str:
    """Quote a SQL identifier for DuckDB, escaping embedded double quotes."""
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def _literal(value: str) -> str:
    """Render a SQL string literal for DuckDB, escaping embedded single quotes."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


@dataclass
class SQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SQL CREATE TABLE or VIEW statements.

    Note: this is currently highly geared towards DuckDB.

    Nested ``class_derivations`` compile to DuckDB ``STRUCT`` values rather than
    being normalized into side tables, so a nested field is a column access for
    consumers rather than a join. Nested shape and cardinality are read from
    ``target_schemaview`` — the *real* target schema, not
    :meth:`Compiler.derived_target_schemaview`, which does not derive nested
    classes and reports every nested slot as a plain ``string``.
    """

    target_schemaview: SchemaView | None = None
    """A view over the schema describing the target.  Required for nested derivations."""

    add_if_not_exists: bool = True
    new_table_when_transforming: bool = False

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        compiled = CompiledSpecification()
        for cd in specification.class_derivations:
            self.compile_class(compiled, cd, specification)
        return compiled

    def compile_class(
        self,
        compiled: CompiledSpecification,
        cd: ClassDerivation,
        specification: TransformationSpecification,
    ) -> None:
        """
        Compile a class derivation to SQL.

        :param compiled: (modified in place)
        :param cd:
        :param specification:
        :return:
        """
        col_names = []
        col_trs = []
        for sd in cd.slot_derivations.values():
            if sd.hide:
                continue
            col_names.append(sd.name)
            col_trs.append(self.compile_slot_derivation(sd, cd, cd.name, PRIMARY_ALIAS))
        if not col_trs:
            return
        stmt = ""
        if self.new_table_when_transforming:
            stmt += "CREATE TABLE "
            if self.add_if_not_exists:
                stmt += "IF NOT EXISTS "
            stmt += f"{cd.name} \n"
        else:
            # An explicit column list is required because a specification generally derives
            # only some of the target's columns; a bare INSERT ... SELECT demands all of them.
            columns = ", ".join(_quote(name) for name in col_names)
            stmt += f"INSERT INTO {cd.name} ({columns}) SELECT \n"
        stmt += ", \n".join(col_trs)
        stmt += f" FROM {cd.populated_from or cd.name} AS {PRIMARY_ALIAS}"
        compiled.serialization += f"{stmt};\n"

    def compile_slot_derivation(
        self,
        sd: SlotDerivation,
        parent_cd: ClassDerivation | None = None,
        target_class: str | None = None,
        table_alias: str = PRIMARY_ALIAS,
    ) -> str:
        """
        Compile one slot derivation to a ``<expression> AS <name>`` select item.

        :param sd: The slot derivation to compile.
        :param parent_cd: The class derivation owning *sd*, which carries the join specs
            a cross-table nested derivation needs.
        :param target_class: Name of the target class *sd* belongs to, used to look up the
            target slot's cardinality and range.
        :param table_alias: Alias of the table whose columns *sd* reads.
        :return: A select item.
        """
        if sd.class_derivations:
            expr = self._compile_nested(sd, parent_cd, target_class, table_alias)
            return f"  {expr} AS {_quote(sd.name)}"
        expr = sd.populated_from
        if expr is None:
            expr = sd.name
        expr = f"{table_alias}.{expr}"
        if sd.stringification:
            syntax = sd.stringification.syntax
            delimiter = sd.stringification.delimiter
            if sd.stringification.reversed:
                pass
            # duckdb specific?
            elif syntax == SerializationSyntaxType.JSON:
                expr = f"CAST({expr} AS TEXT)"
            elif delimiter:
                expr = f"STRING_AGG({expr}, {_literal(delimiter)})"
        return f"  {expr} AS {sd.name}"

    def _target_slot(self, slot_name: str, target_class: str | None) -> SlotDefinition:
        """
        Resolve a target slot definition, which carries the nested shape and cardinality.

        :param slot_name: Name of the target slot.
        :param target_class: Name of the target class owning the slot.
        :raises ValueError: If no target schema is available, or the slot is not found.
        """
        if self.target_schemaview is None or target_class is None:
            msg = (
                f"Compiling nested class_derivations for slot {slot_name!r} requires a target "
                "schema; construct SQLCompiler(target_schemaview=...) so the nested STRUCT "
                "shape and cardinality can be resolved."
            )
            raise ValueError(msg)
        slot = self.target_schemaview.induced_slot(slot_name, target_class)
        if slot is None:
            msg = f"Target slot {target_class}.{slot_name} not found in the target schema"
            raise ValueError(msg)
        return slot

    def _compile_nested(
        self,
        sd: SlotDerivation,
        parent_cd: ClassDerivation | None,
        target_class: str | None,
        table_alias: str,
    ) -> str:
        """
        Compile a slot derivation carrying nested ``class_derivations`` to a STRUCT expression.

        Same-row nesting (the nested derivation reads the parent's table) becomes an inline
        struct literal.  Cross-table nesting becomes a correlated subquery over the joined
        table, so multiple multivalued nested slots on one class cannot form a cartesian
        product the way a ``GROUP BY`` over repeated joins would.

        :param sd: The slot derivation declaring nested class derivations.
        :param parent_cd: The class derivation owning *sd*, carrying its join specs.
        :param target_class: Name of the target class *sd* belongs to.
        :param table_alias: Alias of the table the parent derivation reads.
        :return: A DuckDB expression yielding a STRUCT or a list of STRUCTs.
        :raises ValueError: If the nesting cannot be compiled unambiguously.
        """
        target_slot = self._target_slot(sd.name, target_class)
        multivalued = bool(target_slot.multivalued)
        if len(sd.class_derivations) > 1 and not multivalued:
            msg = (
                f"Slot {target_class}.{sd.name} declares {len(sd.class_derivations)} nested "
                "class_derivations but is single-valued in the target schema; only a "
                "multivalued slot can hold more than one derived object."
            )
            raise ValueError(msg)

        parent_source = (parent_cd.populated_from or parent_cd.name) if parent_cd else None
        exprs = [
            self._compile_nested_one(cd, sd, parent_cd, parent_source, table_alias, multivalued, index)
            for index, cd in enumerate(sd.class_derivations)
        ]
        if not multivalued:
            return exprs[0]
        if len(exprs) == 1:
            return exprs[0]
        return f"list_concat({', '.join(exprs)})"

    def _compile_nested_one(
        self,
        cd: ClassDerivation,
        sd: SlotDerivation,
        parent_cd: ClassDerivation | None,
        parent_source: str | None,
        table_alias: str,
        multivalued: bool,
        index: int,
    ) -> str:
        """
        Compile a single nested class derivation to a struct (or list-of-struct) expression.

        :param cd: The nested class derivation.
        :param sd: The slot derivation declaring it.
        :param parent_cd: The class derivation owning *sd*, carrying its join specs.
        :param parent_source: The parent derivation's source table.
        :param table_alias: Alias of the table the parent derivation reads.
        :param multivalued: Whether the target slot holds a list.
        :param index: Position of *cd* among the slot's nested derivations, used to keep
            generated table aliases unique.
        :return: A DuckDB expression.
        :raises ValueError: If a cross-table nesting has no join spec to resolve it.
        """
        nested_source = cd.populated_from or cd.name
        if nested_source == parent_source:
            struct = self._struct_literal(cd, table_alias)
            return f"list_value({struct})" if multivalued else struct

        joins = parent_cd.joins if parent_cd else None
        if not joins or nested_source not in joins:
            msg = (
                f"Nested class {cd.name!r} has populated_from={nested_source!r} which differs "
                f"from parent populated_from={parent_source!r}, but no join is declared for it. "
                "Add an explicit joins: block to the parent class derivation."
            )
            raise ValueError(msg)
        source_key, lookup_key = join_keys(joins[nested_source])
        nested_alias = f"{table_alias}_j{index}"
        struct = self._struct_literal(cd, nested_alias)
        projection = f"list({struct})" if multivalued else struct
        subquery = (
            f"SELECT {projection} FROM {nested_source} AS {nested_alias} "
            f"WHERE {nested_alias}.{lookup_key} = {table_alias}.{source_key}"
        )
        if multivalued:
            # A join miss yields an empty list rather than NULL, matching the Python
            # backend, which appends nothing and assigns the empty list (see #217).
            return f"COALESCE(({subquery}), [])"
        return f"({subquery} LIMIT 1)"

    def _struct_literal(self, cd: ClassDerivation, table_alias: str) -> str:
        """
        Render a nested class derivation's slots as a DuckDB struct literal.

        DuckDB casts struct literals to a declared STRUCT column by field name, so the
        field order here need not match the column's declared order.

        :param cd: The nested class derivation.
        :param table_alias: Alias of the table its slots read.
        :return: A DuckDB struct literal.
        """
        fields = []
        for nested_sd in cd.slot_derivations.values():
            if nested_sd.hide:
                continue
            if nested_sd.class_derivations:
                value = self._compile_nested(nested_sd, cd, cd.name, table_alias)
            else:
                value = f"{table_alias}.{nested_sd.populated_from or nested_sd.name}"
            fields.append(f"{_literal(nested_sd.name)}: {value}")
        if not fields:
            msg = f"Nested class derivation {cd.name!r} has no visible slot derivations"
            raise ValueError(msg)
        return "{" + ", ".join(fields) + "}"

    def create_ddl(self, schemaview: SchemaView) -> str:
        """
        Create DDL for the entire schema.

        Note core LinkML has a SQL DDL generator, but this is primarily for pure relational models.

        DuckDB allows complex datatypes.

        TODO: move to LinkML core
        :param schemaview:
        :return:
        """
        ddl = []
        for c in schemaview.all_classes().values():
            if c.mixin or c.abstract:
                continue
            col_strs = []
            for s in schemaview.class_induced_slots(c.name):
                col_strs.append(f"  {s.name} {self.sql_type(s, schemaview)}")
            if not col_strs:
                continue
            ddl.append(f"CREATE TABLE IF NOT EXISTS {c.name} (")
            ddl.append(",\n".join(col_strs))
            ddl.append(");")
        return "\n".join(ddl)

    def create_target_ddl(self, specification: TransformationSpecification) -> str:
        target_sv = self.derived_target_schemaview(specification)
        return self.create_ddl(target_sv)

    def sql_type(self, slot: SlotDefinition, schemaview: SchemaView, _enclosing: frozenset[str] = frozenset()) -> str:
        """
        Map LinkML types to DuckDB SQL types.

        An inlined class-ranged slot carries a nested object and becomes a ``STRUCT`` of that
        class's own columns; a non-inlined one is a reference and becomes the identifier's type.

        :param slot: The slot to type.
        :param schemaview: Schema the slot's range is resolved against.
        :param _enclosing: Classes already being expanded, guarding against recursive ranges.
        :return: A DuckDB type.
        """
        typ = "TEXT"
        if slot.range:
            if slot.range in LINKML_TO_SQL_TYPE_MAP:
                typ = LINKML_TO_SQL_TYPE_MAP.get(slot.range, typ)
            elif slot.range in schemaview.all_classes():
                if slot.inlined or slot.inlined_as_list:
                    typ = self.struct_type(slot.range, schemaview, _enclosing)
                else:
                    typ = self._reference_type(slot.range, schemaview)

        if slot.multivalued:
            typ = f"{typ}[]"
        return typ

    def struct_type(
        self,
        class_name: str,
        schemaview: SchemaView,
        _enclosing: frozenset[str] = frozenset(),
    ) -> str:
        """
        Render a class as a DuckDB ``STRUCT`` type over its induced slots.

        :param class_name: The class to expand.
        :param schemaview: Schema the class is resolved against.
        :param _enclosing: Classes already being expanded.  A range that recurses into one of
            them degrades to ``JSON``, since a STRUCT type cannot be infinitely deep.
        :return: A DuckDB ``STRUCT(...)`` type, or ``JSON`` for a recursive range.
        """
        if class_name in _enclosing:
            return "JSON"
        nested = _enclosing | {class_name}
        field_strs = [
            f"{_quote(s.name)} {self.sql_type(s, schemaview, nested)}"
            for s in schemaview.class_induced_slots(class_name)
        ]
        if not field_strs:
            return "JSON"
        return f"STRUCT({', '.join(field_strs)})"

    def _reference_type(self, class_name: str, schemaview: SchemaView) -> str:
        """
        Type of a non-inlined reference to *class_name*: the type of its identifier.

        :param class_name: The referenced class.
        :param schemaview: Schema the class is resolved against.
        :return: A DuckDB type.
        """
        for s in schemaview.class_induced_slots(class_name):
            if s.identifier or s.key:
                return LINKML_TO_SQL_TYPE_MAP.get(s.range, "TEXT")
        return "TEXT"
