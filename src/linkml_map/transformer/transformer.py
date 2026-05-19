"""Transformers transform objects from one class to another using a transformation specification."""

import logging
import warnings
from abc import ABC
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from curies import Converter
from linkml_runtime import SchemaView
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview
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
from linkml_map.utils.join_utils import pick_join_key
from linkml_map.utils.schema_patch import apply_schema_patch

logger = logging.getLogger(__name__)


def _iter_values_or_list(container: Any) -> Iterator[dict[str, Any]]:
    """Yield each dict in a derivations section (dict-keyed or list form).

    Caller assumes shape has been canonicalized (i.e., the SHAPE phase of
    ``Transformer._normalize_spec_dict`` has run), so compact-key list
    items are already expanded.
    """
    if isinstance(container, dict):
        for v in container.values():
            if isinstance(v, dict):
                yield v
    elif isinstance(container, list):
        for item in container:
            if isinstance(item, dict):
                yield item


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

    1. **Load-time normalization** (``_normalize_spec_dict``): Structural fixes
       applied to a raw dict before Pydantic instantiation — YAML quirk handling,
       ``$ref`` expansion, dict-to-list conversion. Does not require a source schema.
       All entry points (``load_transformer_specification``,
       ``create_transformer_specification``, ``Session``, ``loaders``) go through
       this single method.

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
    with the ``ValidationMessage`` list returned by ``_normalize_spec_dict``.
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
            self.spec_messages = self._normalize_spec_dict(obj)
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
        self.spec_messages = self._normalize_spec_dict(obj)
        self.specification = TransformationSpecification(**obj)

    @classmethod
    def normalize_transform_spec(cls, obj: dict[str, Any], normalizer: ReferenceValidator) -> dict:
        """Shape-canonicalize class_derivations recursively.

        Pure shape work — no field migrations. ``object_derivations``
        flattening and ``populated_from`` inheritance happen in the MIGRATE
        phase of :meth:`_normalize_spec_dict` so the SCAN phase between
        them sees the user's original field values.
        """
        obj = normalizer.normalize(obj)

        class_derivations = obj.get("class_derivations", [])
        if isinstance(class_derivations, dict):
            cd_iter = class_derivations.values()
        else:
            cd_iter = class_derivations
        for class_spec in cd_iter:
            if not isinstance(class_spec, dict):
                continue
            slot_derivations = class_spec.get("slot_derivations", {})
            for slot_name, slot_spec in slot_derivations.items():
                if slot_spec.get("value") is not None and slot_spec.get("range") is None:
                    slot_spec["range"] = "string"
                cls._normalize_slot_class_derivations(slot_name, slot_spec, normalizer)
        return obj

    @classmethod
    def _normalize_slot_class_derivations(
        cls,
        slot_name: str,
        slot_spec: dict[str, Any],
        normalizer: ReferenceValidator,
    ) -> None:
        """Shape-canonicalize the ``class_derivations`` on a slot, recursively.

        Two steps, applied recursively to nested slots:

        1. Expand compact-key entries (``- Condition: {...}`` →
           ``{name: Condition, ...}``).
        2. Run the normalizer on each class derivation entry so dict-keyed
           ``slot_derivations`` get ``name`` injected and other shape
           canonicalization happens.

        Pure shape — no field semantics. ``object_derivations`` flattening
        and ``populated_from`` inheritance live in the MIGRATE phase of
        :meth:`_normalize_spec_dict`, not here, so the SCAN phase sees the
        user's original field values.
        """
        slot_cd = slot_spec.get("class_derivations")
        if not isinstance(slot_cd, list):
            return

        cls._expand_compact_keys(slot_cd)

        for cd_entry in slot_cd:
            if not isinstance(cd_entry, dict):
                continue
            normalized = normalizer.normalize(cd_entry)
            cd_entry.clear()
            cd_entry.update(normalized)
            for nested_name, nested_sd in cd_entry.get("slot_derivations", {}).items():
                if isinstance(nested_sd, dict):
                    cls._normalize_slot_class_derivations(nested_name, nested_sd, normalizer)

    @classmethod
    def _normalize_spec_dict(cls, obj: dict[str, Any], *, silent: bool = False) -> list[Any]:
        """Normalize a raw specification dict in place. Return scan messages.

        Three clean phases, ordered so the SCAN sees a canonical shape with
        the user's original field values:

        1. **SHAPE** — pure structural canonicalization, no field semantics.
           Expands compact-key list forms everywhere they can appear
           (top-level class/enum derivations, nested class_derivations in
           slots, OD-inner class_derivations, PV-level lists), then runs
           ``ReferenceValidator`` for dict↔list canonicalization and name
           injection.
        2. **SCAN** — :func:`linkml_map.validator.check_deprecated_fields`
           walks the canonical shape, returning ``ValidationMessage``
           records for deprecated-field usage and ambiguous combinations.
           Unless ``silent``, deprecation warnings fire as Python
           ``DeprecationWarning`` and conflict errors raise
           :class:`~linkml_map.transformer.errors.SpecificationError`.
        3. **MIGRATE** — all field semantics in one pass:
           ``object_derivations`` flatten, ``populated_from`` inheritance
           from parent class, PV scalar → list, PV explicit-``None`` strip,
           PV ``sources`` → ``populated_from`` (clearing ``sources``).

        After this method, ``sources`` no longer appears on any
        ``PermissibleValueDerivation`` — the runtime can rely on
        ``populated_from`` as the single source of truth.

        :param obj: Raw specification dict (e.g. from YAML or user code).
        :param silent: When ``True``, neither emit warnings nor raise on
            errors — return them in the message list instead. Used by the
            validator path so it can surface findings as
            ``ValidationMessage`` records.
        :returns: A list of :class:`ValidationMessage` records from the scan.
        """
        from linkml_map.transformer.errors import SpecificationError
        from linkml_map.validator import check_deprecated_fields

        # SHAPE
        cls._shape_normalize(obj)

        # SCAN
        messages = check_deprecated_fields(obj)

        if not silent:
            errors = [m for m in messages if m.severity == "error"]
            if errors:
                raise SpecificationError("; ".join(m.message for m in errors))
            for m in messages:
                if m.category == "deprecated":
                    warnings.warn(m.message, DeprecationWarning, stacklevel=3)

        # MIGRATE
        cls._flatten_object_derivations(obj)
        cls._inherit_populated_from(obj)
        cls._coerce_pv_populated_from_to_list(obj)
        cls._migrate_pv_sources_to_populated_from(obj)

        return messages

    @classmethod
    def _shape_normalize(cls, obj: dict[str, Any]) -> None:
        """Canonicalize the structural shape of every derivation section.

        Expands compact-key list forms in every derivation-section location
        (including OD-inner class_derivations and PV-level lists, which
        ``ReferenceValidator`` doesn't canonicalize correctly), then runs
        ``ReferenceValidator`` for dict↔list canonicalization and name
        injection. No field semantics are mutated.
        """
        cls._pre_shape_expand_compact_keys(obj)
        normalizer = ReferenceValidator(package_schemaview("linkml_map.datamodel.transformer_model"))
        normalizer.expand_all = True
        normalized = cls.normalize_transform_spec(obj, normalizer)
        obj.clear()
        obj.update(normalized)

    @classmethod
    def _pre_shape_expand_compact_keys(cls, obj: dict[str, Any]) -> None:
        """Recursively expand compact-key list forms before ReferenceValidator.

        Compact-key list form (``[{Name: {body}}]``) is a linkml-map convention,
        not a documented LinkML collection form. ``ReferenceValidator``
        therefore doesn't canonicalize it consistently — list-typed fields
        (top-level class_derivations) are left as-is, and dict-typed fields
        (permissible_value_derivations) get mangled to ``{None: ...}``. This
        pre-pass converts compact-key items to explicit-name form everywhere
        the linkml-map schema accepts a derivation section, so RV sees only
        LinkML-canonical input.

        See https://github.com/linkml/linkml/issues/3529 for the upstream
        behavior. The local pre-expansion makes us independent of how (or
        whether) that gets resolved.
        """
        cls._preprocess_class_derivations(obj)
        cls._preprocess_enum_derivations(obj)
        for cd in _iter_values_or_list(obj.get("class_derivations")):
            cls._expand_compact_keys_in_class_deriv(cd)

    @classmethod
    def _expand_compact_keys_in_class_deriv(cls, cd: dict[str, Any]) -> None:
        """Expand compact-key list forms in a class derivation, recursively."""
        for sd in _iter_values_or_list(cd.get("slot_derivations")):
            # Slot's own nested class_derivations (list-with-compact-keys form)
            nested_cds = sd.get("class_derivations")
            if isinstance(nested_cds, list):
                cls._expand_compact_keys(nested_cds)
            for ncd in _iter_values_or_list(nested_cds):
                cls._expand_compact_keys_in_class_deriv(ncd)
            # OD-inner class_derivations (deprecated form; flattened in MIGRATE)
            ods = sd.get("object_derivations")
            if isinstance(ods, list):
                for od in ods:
                    if not isinstance(od, dict):
                        continue
                    od_cds = od.get("class_derivations")
                    if isinstance(od_cds, list):
                        cls._expand_compact_keys(od_cds)
                    for ncd in _iter_values_or_list(od_cds):
                        cls._expand_compact_keys_in_class_deriv(ncd)

    @staticmethod
    def _preprocess_enum_derivations(obj: dict[str, Any]) -> None:
        """Pre-process top-level enum_derivations and their PV sections.

        Handles two compact-key cases ReferenceValidator doesn't:
        list-form enum_derivations with ``{Name: {...}}`` items, and
        list-form permissible_value_derivations with the same shape (which
        RV otherwise mangles into ``{None: ...}``).
        """
        eds = obj.get("enum_derivations")
        if isinstance(eds, dict):
            for k, v in eds.items():
                if v is None:
                    eds[k] = {}
        elif isinstance(eds, list):
            Transformer._expand_compact_keys(eds)
        for ed in _iter_values_or_list(obj.get("enum_derivations")):
            pvs = ed.get("permissible_value_derivations")
            if isinstance(pvs, list):
                Transformer._expand_compact_keys(pvs)

    @classmethod
    def _flatten_object_derivations(cls, obj: dict[str, Any]) -> None:
        """Flatten ``object_derivations`` into ``class_derivations`` on every slot.

        Conflicting specs (both ``object_derivations`` and ``class_derivations``
        set) are caught upstream by the SCAN phase as ``severity="error"``,
        so this method assumes a non-conflicting input.
        """
        for cd in _iter_values_or_list(obj.get("class_derivations")):
            cls._flatten_ods_in_class_deriv(cd)

    @classmethod
    def _flatten_ods_in_class_deriv(cls, cd: dict[str, Any]) -> None:
        """Recursively walk a class derivation, flattening OD on each slot."""
        for sd in _iter_values_or_list(cd.get("slot_derivations")):
            ods = sd.get("object_derivations")
            if ods:
                flattened: list[dict[str, Any]] = []
                for od in ods:
                    if not isinstance(od, dict):
                        continue
                    od_cd = od.get("class_derivations", {})
                    if isinstance(od_cd, dict):
                        for name, body in od_cd.items():
                            entry = body if isinstance(body, dict) else {}
                            entry.setdefault("name", name)
                            flattened.append(entry)
                    elif isinstance(od_cd, list):
                        flattened.extend(od_cd)
                sd["class_derivations"] = flattened
                del sd["object_derivations"]
            for ncd in _iter_values_or_list(sd.get("class_derivations")):
                cls._flatten_ods_in_class_deriv(ncd)

    @classmethod
    def _inherit_populated_from(cls, obj: dict[str, Any]) -> None:
        """Propagate ``populated_from`` from parent class down to nested CDs.

        Walks each class_derivation's slot_derivations.class_derivations; if
        a nested CD doesn't set ``populated_from``, it inherits from the
        outer class's value. Recurses through arbitrarily deep nesting.
        """
        for cd in _iter_values_or_list(obj.get("class_derivations")):
            cls._inherit_pf_in_slots(cd.get("slot_derivations"), cd.get("populated_from"))

    @classmethod
    def _inherit_pf_in_slots(cls, slots: Any, parent_pf: str | None) -> None:
        """Recursively inherit populated_from into nested class_derivations."""
        for sd in _iter_values_or_list(slots):
            for ncd in _iter_values_or_list(sd.get("class_derivations")):
                if not ncd.get("populated_from") and parent_pf:
                    ncd["populated_from"] = parent_pf
                cls._inherit_pf_in_slots(ncd.get("slot_derivations"), ncd.get("populated_from"))

    @staticmethod
    def _iter_pv_derivations(obj: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Yield each PermissibleValueDerivation dict in ``obj`` for in-place mutation."""
        eds = obj.get("enum_derivations")
        if isinstance(eds, dict):
            ed_iter: Any = eds.values()
        elif isinstance(eds, list):
            ed_iter = eds
        else:
            return
        for ed in ed_iter:
            if not isinstance(ed, dict):
                continue
            pvds = ed.get("permissible_value_derivations")
            if isinstance(pvds, dict):
                pvd_iter: Any = pvds.values()
            elif isinstance(pvds, list):
                pvd_iter = pvds
            else:
                continue
            for pvd in pvd_iter:
                if isinstance(pvd, dict):
                    yield pvd

    @classmethod
    def _coerce_pv_populated_from_to_list(cls, obj: dict[str, Any]) -> None:
        """Coerce ``populated_from`` to a list on each PV deriv.

        Input shapes handled:

        * Scalar string: wrapped to a one-element list (user convenience that
          pydantic would otherwise reject for a multivalued field).
        * Explicit ``None`` or ``[None]`` (``populated_from:`` with no YAML
          value, possibly already wrapped to a list by ``ReferenceValidator``):
          the key is removed so pydantic uses the ``default_factory=list``
          default — treats "explicitly set to nothing" as "unset".
        * List: left as-is.
        """
        for pvd in cls._iter_pv_derivations(obj):
            if "populated_from" not in pvd:
                continue
            pf = pvd["populated_from"]
            if pf is None or (isinstance(pf, list) and not any(pf)):
                del pvd["populated_from"]
            elif isinstance(pf, str):
                pvd["populated_from"] = [pf]

    @classmethod
    def _migrate_pv_sources_to_populated_from(cls, obj: dict[str, Any]) -> None:
        """Move deprecated ``sources`` into ``populated_from`` on PV derivs.

        Applied after the pre-normalize scan has already detected and reported
        any ``sources`` usage and any ``sources`` + ``populated_from`` conflicts.
        For each PV deriv with ``sources`` set, copies into ``populated_from``
        (if not already set) and clears the ``sources`` key. Post-condition:
        no PV has ``sources`` set. The runtime can therefore rely on
        ``populated_from`` as the single source of truth and ignore ``sources``.
        """
        for pvd in cls._iter_pv_derivations(obj):
            srcs = pvd.pop("sources", None)
            if srcs and not pvd.get("populated_from"):
                pvd["populated_from"] = list(srcs)

    @staticmethod
    def _expand_compact_keys(items: list[dict[str, Any]]) -> None:
        """Expand YAML compact-key dicts in a list in place.

        Converts ``{"Condition": {"populated_from": "x"}}`` →
        ``{"name": "Condition", "populated_from": "x"}``.
        Skips items whose sole key is ``"name"`` (already expanded).
        """
        for i, item in enumerate(items):
            if isinstance(item, dict) and len(item) == 1:
                key, val = next(iter(item.items()))
                if key != "name" and isinstance(val, dict | type(None)):
                    expanded = val if val is not None else {}
                    expanded.setdefault("name", key)
                    items[i] = expanded

    @staticmethod
    def _preprocess_class_derivations(obj: dict[str, Any]) -> None:
        """Pre-process top-level class_derivations before ReferenceValidator normalization.

        Handles two cases:
        1. Dict format with None values (e.g. ``Entity:`` with no body) — replace
           with empty dicts so ReferenceValidator.ensure_list doesn't choke.
        2. List format with compact keys — delegate to ``_expand_compact_keys``.
        """
        cd = obj.get("class_derivations")
        if isinstance(cd, dict):
            for k, v in cd.items():
                if v is None:
                    cd[k] = {}
        elif isinstance(cd, list):
            Transformer._expand_compact_keys(cd)

    def create_transformer_specification(self, obj: dict[str, Any]) -> None:
        """
        Create specification from a dict.

        TODO: this will no longer be necessary when pydantic supports inlined as dict

        :param path:
        :return:
        """
        self.spec_messages = self._normalize_spec_dict(obj)
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
            self._derived_specification = deepcopy(self.specification)
            induce_missing_values(self._derived_specification, self.source_schemaview)
            self._synthesize_implicit_joins(self._derived_specification)
        return self._derived_specification

    def _synthesize_implicit_joins(self, spec: TransformationSpecification) -> None:
        """Add explicit join specs for nested class_derivations with cross-table references.

        Walks all nested class_derivations. When a nested CD has a different
        ``populated_from`` than its parent and no explicit ``joins:`` block,
        synthesizes an ``AliasedClass`` join entry on the parent CD using
        :func:`pick_join_key` to determine the join column.

        Mutates *spec* in place.

        :param spec: The derived specification to augment.
        """
        sv = self.source_schemaview
        if sv is None:
            return

        for cd in spec.class_derivations:
            parent_source = cd.populated_from or cd.name
            self._walk_and_synthesize_joins(cd, parent_source, sv)

    def _walk_and_synthesize_joins(
        self,
        class_deriv: ClassDerivation,
        parent_source: str,
        sv: SchemaView,
    ) -> None:
        """Recursively walk slot_derivations and synthesize joins on parent CDs.

        :param class_deriv: The parent ClassDerivation to add joins to.
        :param parent_source: The parent's populated_from.
        :param sv: Source schema view.
        """
        for sd in class_deriv.slot_derivations.values():
            if not sd.class_derivations:
                continue
            for nested_cd in sd.class_derivations:
                nested_source = nested_cd.populated_from or parent_source

                # Synthesize a join when the nested CD references a different table
                if nested_source != parent_source:
                    join_key = pick_join_key(sv, parent_source, nested_source)
                    if join_key is not None:
                        if class_deriv.joins is None:
                            class_deriv.joins = {}
                        if nested_source not in class_deriv.joins:
                            class_deriv.joins[nested_source] = AliasedClass(
                                alias=nested_source,
                                join_on=join_key,
                            )
                            logger.info(
                                "Synthesized implicit join: %s.joins[%r] on column %r",
                                class_deriv.name,
                                nested_source,
                                join_key,
                            )

                # Always recurse into nested CD's own slots
                if nested_cd.slot_derivations:
                    self._walk_and_synthesize_joins(nested_cd, nested_source, sv)

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
