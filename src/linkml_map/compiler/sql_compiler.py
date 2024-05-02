from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition

from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SerializationSyntaxType,
    TransformationSpecification,
)

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


class SQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SQL CREATE TABLE or VIEW statements.

    Note: this is currently highly geared towards DuckDB.
    """

    add_if_not_exists: bool = True
    new_table_when_transforming: bool = False

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        compiled = CompiledSpecification()
        for cd in specification.class_derivations.values():
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
        stmt = ""
        if self.new_table_when_transforming:
            stmt += "CREATE TABLE "
            if self.add_if_not_exists:
                stmt += "IF NOT EXISTS "
            stmt += f"{cd.name} \n"
        else:
            stmt += f"INSERT INTO {cd.name} SELECT \n"
        col_trs = []
        for sd in cd.slot_derivations.values():
            col_trs.append(self.compile_slot_derivation(sd))
        if not col_trs:
            return
        stmt += ", \n".join(col_trs)
        stmt += f" FROM {cd.name}"
        compiled.serialization += f"{stmt};\n"

    def compile_slot_derivation(self, sd) -> str:
        expr = sd.populated_from
        if expr is None:
            expr = sd.name
        if sd.stringification:
            syntax = sd.stringification.syntax
            delimiter = sd.stringification.delimiter
            if sd.stringification.reversed:
                pass
            else:
                # duckdb specific?
                if syntax == SerializationSyntaxType.JSON:
                    expr = f"CAST({expr} AS TEXT)"
                elif delimiter:
                    expr = f"STRING_AGG({expr}, '{delimiter}')"
        return f"  {sd.name} AS {expr}"

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

    def sql_type(self, slot: SlotDefinition, schemaview: SchemaView) -> str:
        """
        Map LinkML types to DuckDB SQL types.

        :param slot:
        :param schemaview:
        :return:
        """
        typ = "TEXT"
        if slot.range:
            if slot.range in LINKML_TO_SQL_TYPE_MAP:
                typ = LINKML_TO_SQL_TYPE_MAP.get(slot.range, typ)
            elif slot.range in schemaview.all_classes():
                if slot.inlined:
                    typ = "TEXT"
                else:
                    # TODO: consider structs
                    typ = "JSON"

        if slot.multivalued:
            typ = f"{typ}[]"
        return typ
