from copy import deepcopy
from dataclasses import dataclass
from typing import Iterator

from jinja2 import Template

from linkml_map.compiler.compiler import Compiler
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    TransformationSpecification,
)
from linkml_map.inference.inference import induce_missing_values

CD_TEMPLATE = """
{% macro gen_slot_derivation_value(sd, var) -%}
{%- if sd.range -%}
derive_{{ sd.range }}({{ var }})
{%- else -%}
{%- if var is not none -%}
{{ var }}
{%- else -%}
None
{%- endif -%}
{%- endif -%}
{%- endmacro %}
{% macro gen_slot_derivation(sd, force_singlevalued=False) -%}
{%- if not force_singlevalued and sd.populated_from and induced_slots[sd.populated_from].multivalued -%}
 [ {{ gen_slot_derivation_value(sd, "x") }} for x in {{ gen_slot_derivation(sd, force_singlevalued=True) }} ]
{%- else -%}
 {%- if sd.populated_from -%}
  source_object.{{ sd.populated_from }}
 {%- elif sd.expr -%}
  {%- if '\n' in sd.expr -%}
 gen_{{ sd.name }}(source_object)
  {%- elif '{' in sd.expr and '}' in sd.expr -%}
  {{ sd.expr|replace('{', '')|replace('}', '') }}
  {%- else -%}
  {{ sd.expr }}
  {%- endif -%}
 {%- else -%}
  None
 {%- endif -%}
{%- endif -%}
{%- endmacro %}
{% macro gen_slot_derivation_defs(sd) -%}
{% if sd.expr and '\n' in sd.expr %}

    def gen_{{ sd.name }}(src):
        target = None
   {%- for line in sd.expr.split('\n') %}
        {{ line }}
   {%- endfor -%}
        return target
{% endif %}
{%- endmacro %}
def derive_{{ cd.name }}(
        source_object: {{ source_module }}.{{ cd.populated_from }}
    ) -> {{ target_module }}.{{ cd.name }}:
    # assign slots
{%- for slot in source_slots %}
    {{ slot.name }} = source_object.{{ slot.name }}
{%- endfor %}
{%-  for sd in cd.slot_derivations.values() -%}
    {{  gen_slot_derivation_defs(sd) }}
{%-  endfor %}

    return tgt.{{ cd.name }}(
        {%- for sd in cd.slot_derivations.values() %}
        {{ sd.name }}={{ gen_slot_derivation(sd) }},
        {%- endfor %}
    )
"""


@dataclass
class PythonCompiler(Compiler):
    """
    Compiles a Transformation Specification to Python code.
    """

    def _compile_header(self, specification: TransformationSpecification) -> str:
        s = ""
        if self.source_python_module:
            s += f"import {self.source_python_module} as src\n"
        if self.target_python_module:
            s += f"import {self.target_python_module} as tgt\n"
        s += "\nNULL = None\n\n"
        return s

    def _compile_iterator(self, specification: TransformationSpecification) -> Iterator[str]:
        specification = deepcopy(specification)
        induce_missing_values(specification, self.source_schemaview)
        for cd in specification.class_derivations.values():
            yield from self._compiled_class_derivations_iter(cd)

    def _compiled_class_derivations_iter(self, cd: ClassDerivation) -> Iterator[str]:
        sv = self.source_schemaview
        if cd.populated_from:
            populated_from = cd.populated_from
        else:
            populated_from = cd.name
        if populated_from not in sv.all_classes():
            return
        induced_slots = {s.name: s for s in sv.class_induced_slots(populated_from)}
        t = Template(CD_TEMPLATE)
        yield t.render(
            cd=cd,
            source_module="src",
            target_module="tgt",
            induced_slots=induced_slots,
            schemaview=sv,
            source_slots=sv.class_induced_slots(populated_from),
        )
