"""Transformers transform objects from one class to another using a transformation specification."""

import logging
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from curies import Converter
from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_map.datamodel.transformer_model import (
    AliasedClass,
    ClassDerivation,
    CollectionType,
    EnumDerivation,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.inference.inference import induce_missing_values
from linkml_map.spec_normalizer import normalize_spec
from linkml_map.utils.eval_utils import FUNCTIONS, INJECTED_EVAL_NAMES
from linkml_map.utils.expression_locations import (
    extract_braced_reference_roots,
    extract_table_references,
    iter_expressions,
)
from linkml_map.utils.join_utils import infer_join_key
from linkml_map.utils.schema_patch import apply_schema_patch

logger = logging.getLogger(__name__)


OBJECT_TYPE = dict[str, Any] | BaseModel | YAMLRoot
"""An object can be a plain python dict, a pydantic object, or a linkml YAMLRoot"""


@dataclass
class Transformer(ABC):
    """
    Base class for all transformers.

    A transformer will generate an instance of a target class from
    an instance of a source class, making use of a specification.

    This is an abstract class. Different implementations will
    subclass this.

    Specification normalization has two phases:

    1. **Load-time normalization**
       (:func:`~linkml_map.spec_normalizer.normalize_spec`): Structural fixes
       applied to a raw dict before Pydantic instantiation — YAML quirk handling,
       ``$ref`` expansion, dict-to-list conversion. Does not require a source schema.
       All entry points (``load_transformer_specification``,
       ``create_transformer_specification``, ``Session``, ``loaders``) go through
       that single function.

    2. **Schema-bind-time induction** (``derived_specification``): Semantic defaults
       inferred from the source schema — ``populated_from``, ``range``, foreign-key
       resolution. Runs lazily on first access to ``derived_specification`` and
       requires ``source_schemaview`` to be set.
    """

    specification: TransformationSpecification = None
    """A specification of how to generate target objects from source objects."""

    source_schemaview: SchemaView = None
    """A view over the schema describing the input/source object."""

    _derived_specification: TransformationSpecification = None
    """A specification with inferred missing values."""

    _source_schema_patched: bool = field(default=False)
    """Flag to track if source schema patches have been applied."""

    target_schemaview: SchemaView | None = None
    """A view over the schema describing the output/target object."""

    unrestricted_eval: bool = field(default=False)
    """Set to True to allow arbitrary evals as part of transformation."""

    strict: bool = field(default=False)
    """Raise on expression references that do not resolve to a schema slot.

    When ``False`` (the default), unresolved names emit a warning and the
    expression evaluator returns ``None`` (preserving SQL-style null
    propagation for legitimate empty values but losing the signal for
    typos). When ``True``, unresolved names raise
    :class:`~linkml_map.transformer.errors.TransformationError`, which
    surfaces typos, stale references, and wrong-table accesses that
    would otherwise produce silent nulls in the output.
    """

    _curie_converter: Converter = None

    spec_messages: list[Any] = field(default_factory=list)
    """Scan messages captured at spec-load time.

    Populated by the three load methods (``load_transformer_specification``,
    ``load_transformer_specifications``, ``create_transformer_specification``)
    with the ``ValidationMessage`` list returned by ``normalize_spec``.
    Pre-flight validation reads these instead of re-scanning the post-migration
    spec, so deprecations whose source fields were cleared by normalization
    (e.g., ``object_derivations``, PV ``sources``) are still surfaced.
    """

    def map_object(self, obj: OBJECT_TYPE, source_type: str | None = None, **kwargs: Any) -> OBJECT_TYPE:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param source_type:
        :return:
        """
        raise NotImplementedError

    def map_database(
        self, source_database: Any, target_database: Any | None = None, **kwargs: dict[str, Any]
    ) -> OBJECT_TYPE:
        """
        Transform source resource.

        :param source_database:
        :param target_database:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def load_source_schema(self, path: str | Path | dict) -> None:
        """
        Set source_schemaview from a schema path.

        :param path:
        """
        if isinstance(path, Path):
            path = str(path)
        self.source_schemaview = SchemaView(path)

    def load_transformer_specification(self, path: str | Path) -> None:
        """
        Set specification from a schema path.

        :param path:
        :return:
        """
        with open(path) as f:
            obj = yaml.safe_load(f)
            self.spec_messages = normalize_spec(obj)
            self.specification = TransformationSpecification(**obj)

    def load_transformer_specifications(self, paths: tuple[str | Path, ...]) -> None:
        """Load and merge multiple transformation spec files into a single specification.

        Accepts file paths and/or directories.  Directories are recursively
        searched for YAML files.  All specs are merged (class_derivations
        appended, enum/slot_derivations unioned by name) and the result is
        set as ``self.specification``.

        :param paths: One or more file or directory paths.
        """
        from linkml_map.utils.spec_merge import load_and_merge_specs

        obj = load_and_merge_specs(paths)
        self.spec_messages = normalize_spec(obj)
        self.specification = TransformationSpecification(**obj)

    def create_transformer_specification(self, obj: dict[str, Any]) -> None:
        """
        Create specification from a dict.

        TODO: this will no longer be necessary when pydantic supports inlined as dict

        :param path:
        :return:
        """
        self.spec_messages = normalize_spec(obj)
        self.specification = TransformationSpecification(**obj)

    def _apply_source_schema_patches(self) -> None:
        """Apply source_schema_patches from specification to source_schemaview."""
        if self._source_schema_patched:
            return
        if self.specification and self.source_schemaview:
            patches = self.specification.source_schema_patches
            if patches:
                apply_schema_patch(self.source_schemaview, patches)
                self.source_schemaview.induced_slot.cache_clear()
        self._source_schema_patched = True

    @property
    def derived_specification(self) -> TransformationSpecification | None:
        """Return the specification with schema-inferred defaults filled in.

        Creates a deep copy of ``self.specification``, applies any source schema
        patches, then calls ``induce_missing_values`` to fill in ``populated_from``,
        ``range``, and other fields that require knowledge of the source schema.
        The result is cached for subsequent access.

        This is the second phase of normalization — see the class docstring for
        the full two-phase pipeline.
        """
        if self._derived_specification is None:
            if self.specification is None:
                return None
            self._apply_source_schema_patches()
            # Build into a local and only cache on full success: synthesis can
            # fail loud (e.g. an un-keyable cross-table reference), and caching a
            # half-synthesized spec would poison every later access.
            derived = deepcopy(self.specification)
            induce_missing_values(derived, self.source_schemaview)
            self._synthesize_implicit_joins(derived)
            self._derived_specification = derived
        return self._derived_specification

    def _synthesize_implicit_joins(self, spec: TransformationSpecification) -> None:
        """Add explicit join specs for every implicit cross-table reference.

        Two kinds of implicit reference are normalized into explicit
        ``AliasedClass`` joins on the enclosing ClassDerivation (the only place
        ``joins:`` can live):

        - a nested class_derivation whose ``populated_from`` is a different table;
        - a ``{Table.col}`` reference in *any* expression on a class derivation or
          its slot derivations (``expr``, ``expression_mappings``, etc.). This
          second case was previously unhandled, which is why an expr-only implicit
          join silently resolved to ``None``.

        Mutates *spec* in place.

        :param spec: The derived specification to augment.
        """
        sv = self.source_schemaview
        if sv is None:
            return

        table_names = set(sv.all_classes())
        for cd in spec.class_derivations:
            parent_source = cd.populated_from or cd.name
            self._walk_and_synthesize_joins(cd, parent_source, sv, table_names, {parent_source})
        # Cross-table refs in derivations with no enclosing class_derivation
        # (top-level enum/permissible-value/slot derivations) have nowhere to host
        # a join — fail fast rather than silently resolve to None.
        self._reject_unhostable_cross_table_refs(spec, table_names)

    def _walk_and_synthesize_joins(
        self,
        class_deriv: ClassDerivation,
        parent_source: str,
        sv: SchemaView,
        table_names: set[str],
        available: set[str],
    ) -> None:
        """Recursively synthesize joins for cross-table references under *class_deriv*.

        :param class_deriv: The ClassDerivation that will host synthesized joins.
        :param parent_source: This derivation's ``populated_from``.
        :param sv: Source schema view.
        :param table_names: All source-schema class names (table candidates).
        :param available: Tables already in scope here (the ancestor source chain
            plus this source) — a reference to one of these is the parent/own row,
            not a new join.
        """
        # Expressions on the class derivation itself and on each slot derivation
        # are hosted on this class derivation.
        self._synthesize_joins_for_expressions(class_deriv, parent_source, class_deriv, sv, table_names, available)
        for sd in class_deriv.slot_derivations.values():
            self._synthesize_joins_for_expressions(class_deriv, parent_source, sd, sv, table_names, available)

            if sd.populated_from and "." in sd.populated_from:
                table_name = sd.populated_from.split(".", 1)[0]
                if table_name not in available and table_name in table_names:
                    self._synthesize_join(class_deriv, parent_source, table_name, sv)

            # object_derivations are flattened into class_derivations at spec-load
            # time (deprecated), so synthesis only needs to walk class_derivations.
            for nested_cd in sd.class_derivations or []:
                nested_source = nested_cd.populated_from or parent_source
                if nested_source != parent_source:
                    self._synthesize_join(class_deriv, parent_source, nested_source, sv)
                if nested_cd.slot_derivations:
                    self._walk_and_synthesize_joins(
                        nested_cd, nested_source, sv, table_names, available | {nested_source}
                    )

    def _synthesize_joins_for_expressions(
        self,
        host_cd: ClassDerivation,
        parent_source: str,
        derivation: Any,
        sv: SchemaView,
        table_names: set[str],
        available: set[str],
    ) -> None:
        """Synthesize joins on *host_cd* for every ``{Table.col}`` in *derivation*'s expressions.

        Tables already in scope (``available``) are the parent/own row and need no join.
        A qualified ``{Name.col}`` whose root is neither a table, an in-scope source, a
        slot on this source, nor a function is an unresolvable reference and fails loud.
        """
        for expression in iter_expressions(derivation):
            for table in extract_table_references(expression, table_names):
                if table not in available:
                    self._synthesize_join(host_cd, parent_source, table, sv, required=True)
            roots = extract_braced_reference_roots(expression)
            self._reject_unknown_qualified_roots(host_cd, parent_source, roots, sv, table_names, available)

    def _reject_unknown_qualified_roots(
        self,
        host_cd: ClassDerivation,
        parent_source: str,
        roots: set[str],
        sv: SchemaView,
        table_names: set[str],
        available: set[str],
    ) -> None:
        """Fail loud on a qualified ``{Name.col}`` whose root resolves to nothing.

        ``Name`` is resolvable when it is a source table, an in-scope source
        (``available``), a declared join alias on *host_cd* (which may differ
        from its ``class_named`` schema class), a slot on *parent_source* (a
        same-row or inlined-object reference), or a known expression function.
        Anything else — a typo or a renamed/missing table — would silently
        resolve to ``None`` at runtime, so surface it at normalization time.

        :raises ValueError: if any qualified root is unresolvable.
        """
        known = (
            table_names
            | available
            | set(host_cd.joins or {})
            | self._source_slot_names(sv, parent_source)
            | set(FUNCTIONS)
            | INJECTED_EVAL_NAMES
        )
        unknown = roots - known
        if unknown:
            msg = (
                f"Expression reference(s) {sorted(unknown)} on class_derivation {host_cd.name!r} "
                f"cannot be resolved: each root must be a source table, a slot on {parent_source!r}, "
                f"or a function. Fix the reference or correct the source schema."
            )
            raise ValueError(msg)

    @staticmethod
    def _source_slot_names(sv: SchemaView, source: str) -> set[str]:
        """Return the induced slot names of *source*, or empty if it is not a class."""
        if source not in sv.all_classes():
            return set()
        return {s.name for s in sv.class_induced_slots(source)}

    def _synthesize_join(
        self,
        class_deriv: ClassDerivation,
        parent_source: str,
        table: str,
        sv: SchemaView,
        *,
        required: bool = False,
    ) -> None:
        """Add an explicit ``AliasedClass`` join for *table* on *class_deriv*.

        No-op when the join is already declared/synthesized. When no join key can
        be inferred, behavior depends on *required*:

        - ``required=True`` (an expression ``{table.col}`` reference): fail loud.
          An expression reference has no runtime safety net — it silently
          resolves to ``None`` — so an un-keyable one must surface here.
        - ``required=False`` (a structural ``populated_from`` join): return
          quietly. The engine reports an un-keyable structural join loudly at
          runtime with a more specific diagnostic (shared/candidate columns).

        :param required: whether an un-keyable reference is a hard error.
        :raises ValueError: if *required* and *table* cannot be keyed.
        """
        if class_deriv.joins and table in class_deriv.joins:
            return
        join_key = infer_join_key(sv, parent_source, table)
        if join_key is None:
            if required:
                msg = (
                    f"Cross-table reference to {table!r} from {parent_source!r} on class_derivation "
                    f"{class_deriv.name!r} cannot be joined: no shared join key could be inferred. "
                    f"Declare an explicit 'joins:' entry with 'join_on' (or 'source_key'/'lookup_key')."
                )
                raise ValueError(msg)
            return
        if class_deriv.joins is None:
            class_deriv.joins = {}
        class_deriv.joins[table] = AliasedClass(alias=table, join_on=join_key)
        logger.info(
            "Synthesized implicit join: %s.joins[%r] on column %r",
            class_deriv.name,
            table,
            join_key,
        )

    def _reject_unhostable_cross_table_refs(self, spec: TransformationSpecification, table_names: set[str]) -> None:
        """Fail fast on a cross-table reference that has no class_derivation to host its join.

        Enum, permissible-value, and top-level slot derivations are not nested
        under a ClassDerivation, so a cross-table reference in one of them cannot
        be turned into a ``joins:`` entry. Covers both an expression ``{Table.col}``
        and a structural ``populated_from: Table.col``; surface either rather than
        letting it silently resolve to ``None`` at runtime.

        :raises ValueError: if such a reference is found.
        """

        def check(kind: str, name: str | None, derivation: Any) -> None:  # noqa: ANN401
            refs: set[str] = set()
            for expression in iter_expressions(derivation):
                refs |= extract_table_references(expression, table_names)
            # populated_from is list-form on permissible-value derivations.
            populated_from = getattr(derivation, "populated_from", None)
            pf_values = populated_from if isinstance(populated_from, list) else [populated_from]
            for pf in pf_values:
                if pf and "." in pf:
                    table = pf.split(".", 1)[0]
                    if table in table_names:
                        refs.add(table)
            if refs:
                msg = (
                    f"Cross-table reference(s) {sorted(refs)} in {kind} {name!r} cannot be "
                    f"joined: only class_derivations can host joins. Move the derivation under "
                    f"a class_derivation, or reference only same-row columns."
                )
                raise ValueError(msg)

        for enum_derivation in self._values(spec.enum_derivations):
            check("enum_derivation", enum_derivation.name, enum_derivation)
            for pv_derivation in self._values(enum_derivation.permissible_value_derivations):
                check("permissible_value_derivation", pv_derivation.name, pv_derivation)
        for slot_derivation in self._values(spec.slot_derivations):
            check("top-level slot_derivation", slot_derivation.name, slot_derivation)

    @staticmethod
    def _values(collection: Any) -> list:  # noqa: ANN401 - dict- or list-form linkml collection
        """Return the members of a linkml multivalued collection, whether dict- or list-form."""
        if not collection:
            return []
        if hasattr(collection, "values"):
            return list(collection.values())
        return list(collection)

    def _get_class_derivation(self, target_class_name: str) -> ClassDerivation:
        spec = self.derived_specification
        matching_tgt_class_derivs = [
            deriv
            for deriv in spec.class_derivations
            if deriv.populated_from == target_class_name
            or (not deriv.populated_from and target_class_name == deriv.name)
        ]
        logger.debug(f"Target class derivations={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            msg = f"Could not find class derivation for {target_class_name} (results={len(matching_tgt_class_derivs)})"
            raise ValueError(msg)
        cd = matching_tgt_class_derivs[0]
        ancmap = self._class_derivation_ancestors(cd)
        if ancmap:
            cd = deepcopy(cd)
            for ancestor in ancmap.values():
                for k, v in ancestor.__dict__.items():
                    if v is not None and v != []:
                        curr_v = getattr(cd, k, None)
                        if isinstance(curr_v, list):
                            curr_v.extend(v)
                        elif isinstance(curr_v, dict):
                            curr_v.update({**v, **curr_v})
                        elif curr_v is None:
                            setattr(cd, k, v)
        return cd

    def _find_class_derivation_by_name(self, name: str) -> ClassDerivation:
        """Look up a class derivation by name from the specification.

        Returns the first match when multiple derivations share the same name.
        """
        for cd in self.specification.class_derivations:
            if cd.name == name:
                return cd
        msg = f"No class derivation named '{name}'"
        raise KeyError(msg)

    def _class_derivation_ancestors(self, cd: ClassDerivation) -> dict[str, ClassDerivation]:
        """
        Return a map of all class derivations that are ancestors of the given class derivation.

        :param cd:
        :return:
        """
        ancestors = {}
        parents = cd.mixins + ([cd.is_a] if cd.is_a else [])
        for parent in parents:
            parent_cd = self._find_class_derivation_by_name(parent)
            ancestors[parent] = parent_cd
            ancestors.update(self._class_derivation_ancestors(parent_cd))
        return ancestors

    def _get_enum_derivation(self, target_enum_name: str) -> EnumDerivation:
        spec = self.derived_specification
        matching_tgt_enum_derivs = [
            deriv
            for deriv in spec.enum_derivations.values()
            if deriv.populated_from == target_enum_name or (not deriv.populated_from and target_enum_name == deriv.name)
        ]
        logger.debug(f"Target enum derivations={matching_tgt_enum_derivs}")
        if len(matching_tgt_enum_derivs) != 1:
            msg = f"Could not find what to derive from a source {target_enum_name}"
            raise ValueError(msg)
        return matching_tgt_enum_derivs[0]

    def _is_coerce_to_multivalued(self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation) -> bool:
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as in [
            CollectionType.MultiValued,
            CollectionType.MultiValuedDict,
            CollectionType.MultiValuedDict,
        ]:
            return True
        if slot_derivation.stringification and slot_derivation.stringification.reversed:
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if slot.multivalued:
                return True
        return False

    def _is_coerce_to_singlevalued(self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation) -> bool:
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as == CollectionType(CollectionType.SingleValued):
            return True
        if slot_derivation.stringification and not slot_derivation.stringification.reversed:
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if not slot.multivalued:
                return True
        return False

    def _coerce_datatype(self, v: Any, target_range: str | None) -> Any:
        if target_range is None:
            return v
        if isinstance(v, list):
            return [self._coerce_datatype(v1, target_range) for v1 in v]
        if isinstance(v, dict):
            return {k: self._coerce_datatype(v1, target_range) for k, v1 in v.items()}
        cmap = {
            "integer": int,
            "float": float,
            "string": str,
            "boolean": bool,
        }
        cls = cmap.get(target_range)
        if not cls:
            logger.warning(f"Unknown target range {target_range}")
            return v
        if isinstance(v, cls):
            return v
        return cls(v)

    @property
    def curie_converter(self) -> Converter:
        if not self._curie_converter:
            self._curie_converter = Converter([])
            for prefix in self.source_schemaview.schema.prefixes.values():
                self._curie_converter.add_prefix(prefix.prefix_prefix, prefix.prefix_reference)
            for prefix in self.specification.prefixes.values():
                self._curie_converter.add_prefix(prefix.key, prefix.value)
        return self._curie_converter

    def expand_curie(self, curie: str) -> str:
        return self.curie_converter.expand(curie)

    def compress_uri(self, uri: str) -> str:
        return self.curie_converter.compress(uri)
