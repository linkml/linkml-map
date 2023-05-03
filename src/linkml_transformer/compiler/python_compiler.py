from copy import deepcopy
from typing import Iterator

from jinja2 import Template

from linkml_transformer.compiler.compiler import Compiler
from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation,
    TransformationSpecification,
)
from linkml_transformer.transformer.inference import induce_missing_values

CD_TEMPLATE = """
{% macro gen_slot_derivation_value(sd, var) -%}
{%- if sd.range -%}
derive_{{ sd.range }}({{ var }})
{%- else -%}
{{ var }}
{%- endif -%}
{%- endmacro %}
{% macro gen_slot_derivation(sd, force_singlevalued=False) -%}
{%- if not force_singlevalued and sd.populated_from and induced_slots[sd.populated_from].multivalued -%}
 [ {{ gen_slot_derivation_value(sd, "x") }} for x in {{ gen_slot_derivation(sd, force_singlevalued=True) }} ]
{%- else -%}
 {%- if sd.populated_from -%}
  source_object.{{ sd.populated_from }}
 {%- elif sd.expr -%}
  {{ sd.expr }}
 {%- else -%}
  None
 {%- endif -%}
{%- endif -%}
{%- endmacro %}
def derive_{{ cd.name }}(
        source_object: {{ source_module }}.{{ cd.populated_from }}
    ) -> {{ target_module }}.{{ cd.name }}:
    return {{ cd.populated_from }}(
       {%- for sd in cd.slot_derivations.values() %}
       {{ sd.name }}={{ gen_slot_derivation(sd) }},
       {%- endfor %}
    )

"""


class PythonCompiler(Compiler):
    """
    Compiles a Transformation Specification to Python code.
    """

    def _compile_iterator(self, specification: TransformationSpecification) -> Iterator[str]:
        specification = deepcopy(specification)
        induce_missing_values(specification, self.source_schemaview)
        for cd in specification.class_derivations.values():
            yield from self._yield_compile_class_derivation(cd)

    def _yield_compile_class_derivation(self, cd: ClassDerivation) -> Iterator[str]:
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
        )
