import yaml, textwrap
from linkml_runtime import SchemaView
from linkml_map.transformer.object_transformer import ObjectTransformer

src = textwrap.dedent("""\
id: https://example.org/t
name: t
prefixes: {linkml: https://w3id.org/linkml/}
default_prefix: t
default_range: string
imports: [linkml:types]
classes:
  meas:
    attributes:
      dbGaP_Subject_ID: {identifier: true}
      meas_val: {range: float}
  look:
    attributes:
      dbGaP_Subject_ID: {identifier: true}
      age: {range: integer}
""")
spec = yaml.safe_load(textwrap.dedent("""\
class_derivations:
  Result:
    populated_from: meas
    slot_derivations:
      dotted_age: {populated_from: 'look.age'}
"""))
sv = SchemaView(src)
t = ObjectTransformer()
t.source_schemaview = sv
t.create_transformer_specification(spec)
print("spec created")
ds = t.derived_specification
print("OK", ds)
