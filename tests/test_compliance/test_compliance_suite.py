"""
Transformers compliance test suite.

This is intended to test all features of the LinkML-Transformers language.
Each test focuses on a single feature, and explores different combinations
of schema, transformation specification, and source/target object pairs.

Note that "print" statements are used intentionally here; when this
test is run via pytest with ``-s -q --tb no --disable-warnings`` settings,
the output is a markdown document that can be used as documentation, for
both end users and developers.

This can also be helpful for developers of this test suite: due to
the use of combinatorial exploration using pytest parametrization,
it can be hard to reason through combinations, and some of the generative
code can be abstract. You are encouraged to look at the markdown outputs
to see what is being generated for each test.
"""

import logging
import re
from dataclasses import dataclass
from datetime import date
from types import ModuleType
from typing import Any, Optional, Union

import pytest
from deepdiff import DeepDiff
from linkml.validator import JsonschemaValidationPlugin, Validator
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import Prefix, SchemaDefinition

from linkml_map.compiler.python_compiler import PythonCompiler
from linkml_map.compiler.sql_compiler import SQLCompiler
from linkml_map.datamodel.transformer_model import (
    CollectionType,
    SerializationSyntaxType,
    TransformationSpecification,
)
from linkml_map.functions.unit_conversion import DimensionalityError, UndefinedUnitError
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer

today = date.today()
formatted_date = today.strftime("%Y-%m-%d")

logger = logging.getLogger(__name__)

print(
    f"""
# LinkML-Map Compliance Suite

This is the output from running the full compliance test suite.

```yaml
Time_executed: {formatted_date}
Package: {__file__}
```

It is organized into **Feature Sets** that test a particular feature or group of features,
and **combinations** of different schemas, input objects, and transformation specifications.
This is intended to exhaustively test all combinations of features, and provide informative
output.

Each test is designed to demonstrate:

- data mapping (transformation)
- derived schemas
- inversion (reverse transformation) (in some cases)
- compilation to other frameworks (coming soon)

"""
)


def print_yaml(obj: Any) -> None:
    print("```yaml")
    print(yaml_dumper.dumps(obj))
    print("```\n")


def build_schema(name: str, **kwargs: dict[str, Any]) -> SchemaDefinition:
    schema = SchemaDefinition(id=name, name=name, **kwargs)
    schema.imports.append("linkml:types")
    schema.default_prefix = "test"
    for k, v in [("linkml", "https://w3id.org/linkml/"), ("test", "http://example.org/test/")]:
        schema.prefixes[k] = Prefix(k, v)
    print("**Source Schema**: \n\n")
    print_yaml(schema)
    return schema


def build_transformer(**kwargs: dict[str, Any]) -> TransformationSpecification:
    mapper = ObjectTransformer()
    mapper.create_transformer_specification(kwargs)
    print("**Transformer Specification**:\n\n")
    print_yaml(mapper.specification)
    return mapper.specification


def create_compilers(
    spec: TransformationSpecification, expected_map: dict[ModuleType, str]
) -> None:
    """
    Test compilation of transformation specifications to other languages.

    This test is a placeholder for future development, where the
    transformation specification will be compiled to other languages
    (e.g. SQL, R2RML, etc.)

    :param spec: transformation specification
    :return:
    """
    for compiler_type, expected in expected_map.items():
        compiler = compiler_type()
        compiled_spec = compiler.compile(spec)
        print(f"**Compiled Specification ({compiler_type.__name__})**:\n\n")
        print(compiled_spec.serialization)
        assert expected in compiled_spec.serialization


@dataclass
class State:
    schema_mapper: SchemaMapper = None
    object_transformer: ObjectTransformer = None
    target_object: Any = None


def map_object(
    spec: TransformationSpecification,
    source_object: dict[str, Any],
    expected_target_object: dict[str, Any],
    source_sv: SchemaView,
    invertible: bool = False,  # noqa: FBT001, FBT002
    index: bool = False,  # noqa: FBT001, FBT002
    source_root: Optional[str] = "Container",
    roundtrip_object: Optional[Any] = None,
    raises_error: Optional[Exception] = None,
    supply_source_schema: Optional[bool] = True,
) -> State:
    """
    Map a source object to a target object, and optionally invert the transformation and perform roundtrip.

    :param spec: transformation specification to use in mapping
    :param source_object: object to convert
    :param expected_target_object: expected value of output of transformation
    :param source_sv: source schema view
    :param invertible: True if the transformation is reversible, via derived inverted transformation
    :param index: True if the source object should use an Object Index
    :param source_root: tree root for source schema, if non-default
    :param roundtrip_object: the expected value of passing target object back through inverted transformation
                             (defaults to source object)
    :param raises_error: if not None, the expected error to be raised during transformation
    :return: state object including transformed object plus intermediate objects
    """
    pc = PythonCompiler(source_schemaview=source_sv)
    python_code = pc.compile(spec)
    logger.debug(f"Python Code: {python_code}\n\n")
    # TODO: enable this
    # print("Python Code (Generated)\n\n")
    # print("```python")
    # print(python_code.serialization)
    # print("```\n")
    # mod = python_code.module
    schema_mapper = SchemaMapper(source_schemaview=source_sv)
    target_schema = schema_mapper.derive_schema(spec)
    target_sv = SchemaView(yaml_dumper.dumps(target_schema))
    if supply_source_schema:
        mapper = ObjectTransformer(source_schemaview=source_sv, specification=spec)
    else:
        mapper = ObjectTransformer(specification=spec)
    if index:
        mapper.index(source_object, target=source_root)
    if raises_error:
        with pytest.raises(raises_error):
            target_object = mapper.map_object(source_object)
            # FIXME: should only have a single line in a `pytest.raises` block
            logger.debug(f"Unexpected Target Object: {target_object}")
        target_object = None
    else:
        target_object = mapper.map_object(source_object)
    assert target_object == expected_target_object, (
        f"failed to map {source_object} to {expected_target_object}"
    )
    assert not DeepDiff(target_object, expected_target_object), "unexpected differences"
    print("**Object Transformation**:\n")
    if raises_error:
        print(f"**Expected Error**: {raises_error.__name__}")
    print(" * Source Object:")
    print_yaml(source_object)
    print(" * Target Object:")
    print_yaml(target_object)
    print("**Target Schema (Derived)**:\n\n")
    print_yaml(target_schema)
    if target_object is not None:
        # remove `foo: None` entries
        target_object = {k: v for k, v in target_object.items() if v is not None}
        ensure_validates(target_sv.schema, target_object)
    if invertible and target_object is not None:
        inverter = TransformationSpecificationInverter(
            source_schemaview=source_sv,
            target_schemaview=target_sv,
        )
        inv_spec = inverter.invert(spec)
        print("**Inverted Transformation Specification** (Derived):\n\n")
        print_yaml(inv_spec)
        inv_mapper = ObjectTransformer(source_schemaview=target_sv, specification=inv_spec)
        inv_target_object = inv_mapper.map_object(target_object)
        if roundtrip_object is None:
            roundtrip_object = source_object
        assert inv_target_object == roundtrip_object, (
            f"failed to invert {target_object} to {source_object}"
        )
    return State(
        schema_mapper=schema_mapper,
        object_transformer=mapper,
        target_object=target_object,
    )


def ensure_validates(target_schema: SchemaDefinition, target_object: Any) -> None:
    """Run the JsonSchema validator on a target_object."""
    target_validator = Validator(
        yaml_dumper.dumps(target_schema), validation_plugins=[JsonschemaValidationPlugin()]
    )
    assert list(target_validator.iter_results(target_object)) == [], (
        f"failed to validate {target_object}"
    )


@pytest.fixture
def invocation_tracker(request: pytest.FixtureRequest) -> bool:
    """
    Emit metadata for each invocation of a test function.

    Also emits the docstring for the test function.

    :param request:
    :return:
    """
    node = request.node
    key = "first_invocation_" + node.originalname
    first_invocation = False
    if not hasattr(request.config, key):
        setattr(request.config, key, True)
        test_function = node.function
        print(f"## Feature Set: {node.originalname}\n")
        docstring = test_function.__doc__
        if not docstring:
            msg = f"Test {node.originalname} has no docstring"
            raise AssertionError(msg)
        for line in docstring.split("\n"):
            line = line.strip()
            if line.startswith(":return:"):
                continue
            match = re.match(r":param (\w+):\s*(.*)", line)
            if match:
                pname, pdesc = match.groups()
                if pname == "invocation_tracker":
                    continue
                print(f"* **{pname}**: {pdesc}")
            else:
                print(line)
        first_invocation = True
    print(f"### Combo: {node.name}\n")
    return first_invocation


@pytest.mark.parametrize(
    ("source_datatype", "target_datatype", "source_value", "target_value", "invertible"),
    [
        ("string", "string", "foo", "foo", True),
        ("integer", "integer", 5, 5, True),
        ("string", "integer", "5", 5, True),
        ("integer", "float", 5, 5.0, True),
        ("float", "integer", 5.0, 5, True),
        ("float", "integer", 5.2, 5, False),
        ("integer", "boolean", 5, True, False),
        ("integer", "boolean", 0, False, False),
    ],
)
def test_map_types(
    invocation_tracker,
    source_datatype: str,
    target_datatype: str,
    source_value: Union[str, float],
    target_value: Union[str, float, bool],
    invertible: bool,  # noqa: FBT001
) -> None:
    """
    Test mapping between basic data types.

    This test uses an ultra-minimal schema with a single class and a single attribute,
    the transformation specification maps that attribute onto itself, with a different
    type, demonstrating type coercion.

    Some cases will be trivially isomorphic (where `source_datatype` == `target_datatype`),
    but these are executed anyway.

    :param invocation_tracker: pytest fixture to emit metadata
    :param source_datatype: linkml datatype of source object
    :param target_datatype: linkml datatype of target object
    :param source_value: value of source object
    :param target_value: expected value of slot in target object
    :param invertible: True if the transformation is invertible
    :return:
    """
    print(f"Mapping `{source_datatype}` => `{target_datatype}`\n\n")
    if source_datatype == target_datatype:
        print("Isomorphic mapping: input should equal output\n")
    else:
        print("Should coerce datatype\n")
    classes = {"C": {"attributes": {"s1": {"range": source_datatype}}}}
    schema = build_schema(
        "types",
        classes=classes,
        description="Minimal single-attribute schema for testing datatype mapping",
    )
    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "slot_derivations": {
                "s1": {
                    "populated_from": "s1",
                    "range": target_datatype,
                }
            }
        }
    }
    spec = build_transformer(class_derivations=cds)

    source_object = {"s1": source_value}
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={"s1": target_value},
        source_sv=source_sv,
        invertible=invertible,
    )


@pytest.mark.parametrize(
    ("source_datatype", "target_datatype", "source_value", "target_value", "invertible"),
    [
        (
            "string",
            "string",
            [{"id": "X", "s1": "foo"}, {"id": "Y", "s1": "bar"}],
            {"X": {"s1": "foo"}, "Y": {"s1": "bar"}},
            True,
        ),
        (
            "string",
            "string",
            {"X": {"s1": "foo"}, "Y": {"s1": "bar"}},
            [{"id": "X", "s1": "foo"}, {"id": "Y", "s1": "bar"}],
            True,
        ),
    ],
)
def test_map_collections(
    invocation_tracker,
    source_datatype: str,
    target_datatype: str,
    source_value: Union[list[dict[str, Any]], dict[str, Any]],
    target_value: Union[list[dict[str, Any]], dict[str, Any]],
    invertible: bool,
) -> None:
    """
    Test mapping between collection data types (lists and dicts).

    This makes use of the `cast_collection_as` construct

    :param invocation_tracker:
    :param source_datatype: linkml datatype of source object
    :param target_datatype: linkml datatype of target object
    :param source_value: value of source object
    :param target_value: expected value of slot in target object
    :param invertible: True if the transformation is invertible
    :return:
    """
    print(f"Mapping `{source_datatype}` => `{target_datatype}`\n\n")
    if source_datatype == target_datatype:
        print("Isomorphic mapping: **input must equal output**\n")
    else:
        print("Should coerce datatype\n")
    source_collection_type = (
        CollectionType.MultiValuedList
        if isinstance(source_value, list)
        else CollectionType.MultiValuedDict
    )
    target_collection_type = (
        CollectionType.MultiValuedList
        if isinstance(target_value, list)
        else CollectionType.MultiValuedDict
    )
    classes = {
        "C": {
            "tree_root": True,
            "attributes": {
                "ds": {
                    "range": "D",
                    "inlined": True,
                    "inlined_as_list": source_collection_type == CollectionType.MultiValuedList,
                    "multivalued": True,
                }
            },
        },
        "D": {"attributes": {"id": {"identifier": True}, "s1": {"range": source_datatype}}},
    }
    schema = build_schema(
        "types",
        classes=classes,
        description="Mapping between collection types",
    )
    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "slot_derivations": {
                "ds": {
                    "populated_from": "ds",
                    "dictionary_key": "id" if isinstance(source_value, list) else None,
                    "cast_collection_as": target_collection_type.value,
                }
            }
        },
        "D": {
            "slot_derivations": {
                "id": {
                    "populated_from": "id",
                },
                "s1": {
                    "populated_from": "s1",
                    "range": target_datatype,
                },
            }
        },
    }
    spec = build_transformer(class_derivations=cds)

    source_object = {"ds": source_value}
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={"ds": target_value},
        source_sv=source_sv,
        invertible=invertible,
    )


@pytest.mark.parametrize(
    ("expr", "source_object", "target_value"),
    [
        ("s1 + s2", {"s1": 5, "s2": 6}, 11),
        ("{s1} + {s2}", {"s1": 5, "s2": 6}, 11),
        ("{s1} + {s2}", {"s1": 5}, None),
        ("s1 + s2.s3", {"s1": 5, "s2": {"s3": 6}}, 11),
        ("s1 + s2.s3.s4", {"s1": 5, "s2": {"s3": {"s4": 6}}}, 11),
        ("s1 + s2", {"s1": "a", "s2": "b"}, "ab"),
        ("s1 + s2", {"s1": ["a"], "s2": ["b"]}, ["a", "b"]),
        ("len(s1)", {"s1": ["a"]}, 1),
        ("s1 < s2", {"s1": 5, "s2": 6}, True),
    ],
)
def test_expr(invocation_tracker, expr: str, source_object: Any, target_value: Any) -> None:
    """
    Test transformation using pythonic expressions.

    This test uses a simple source schema with two slots (`s1` and `s2`).
    These are combined using a pythonic expression, to populate the only
    slot in the target schema (called `derived`).

    The values of `s1` and `s2` can be numbers or strings.

    If the expression wraps a slot in `{...}` then the presence of a None
    forces the entire expression to be `None`

    Limitations: At this time, the framework cannot generate a complete
    derived schema or inversion for expressions. This will be fixed
    in future.

    - See also: [LinkML Expressions](https://linkml.io/linkml/schemas/expression-language.html)

    :param invocation_tracker: pytest fixture to emit metadata
    :param expr: pythonic expression
    :param source_object: source object
    :param target_value: expected value of slot in target object
    :return:
    """
    classes = {"C": {"tree_root": True, "attributes": {}}}

    def infer_range(v: Any, typ: Optional[str] = None) -> str:
        if isinstance(v, dict):
            if not typ:
                typ = v.get("type", "D")
            if typ not in classes:
                classes[typ] = {"attributes": {}}
            for k1, v1 in v.items():
                r = infer_range(v1)
                if not isinstance(r, dict):
                    r = {"range": r}
                classes[typ]["attributes"][k1] = r
            return typ
        if isinstance(v, list):
            r = infer_range(v[0])
            return {"range": r, "multivalued": True}
        if isinstance(v, int):
            return "integer"
        if isinstance(v, float):
            return "float"
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, str):
            return "string"
        msg = f"Unknown type {type(v)}"
        raise ValueError(msg)

    infer_range(source_object, typ="C")
    schema = build_schema("expr", classes=classes)

    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "populated_from": "C",
            "slot_derivations": {
                "derived": {
                    "expr": expr,
                }
            },
        }
    }
    spec = build_transformer(class_derivations=cds)
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={"derived": target_value},
        source_sv=source_sv,
        invertible=False,
    )


@pytest.mark.parametrize(
    (
        "source_slot",
        "target_slot",
        "source_unit",
        "target_unit",
        "unit_metaslot",
        "source_value",
        "target_value",
        "err",
        "skip",
    ),
    [
        ("s1", "s1", "m", "cm", "ucum_code", 1.0, 100.0, None, None),
        ("s1", "s1", "m", "cm", "symbol", 1.0, 100.0, None, None),
        ("s1", "s1", "m", "m", "ucum_code", 1.0, 1.0, None, None),
        ("s1", "s1", "a", "mo", "ucum_code", 10.0, 120.0, None, None),
        ("s1", "s1", "a", "mo", "symbol", 10.0, None, UndefinedUnitError, None),
        ("s1", "s1", "m", "ml", "ucum_code", 1.0, None, DimensionalityError, None),
        ("s1", "s1", "m", "pinknoodles", "ucum_code", 1.0, None, UndefinedUnitError, None),
        ("s1", "s1", "ml", "m", "ucum_code", 1.0, None, DimensionalityError, None),
        ("s1", "s1", "pinknoodles", "m", "ucum_code", 1.0, None, UndefinedUnitError, None),
        ("s1", "s1", "m/s", "cm/s", "ucum_code", 1.0, 100.0, None, None),
        ("s1", "s1", "m.s-1", "cm.s-1", "ucum_code", 1.0, 100.0, None, None),
        (
            "s1",
            "s1",
            "g.m2-1",
            "kg.m2-1",
            "ucum_code",
            1.0,
            0.001,
            None,
            "https://github.com/dalito/ucumvert/issues/8",
        ),
        ("height_in_m", "height_in_cm", "m", "cm", "ucum_code", 1.0, 100.0, None, None),
        ("s1", "s1", "m[H2O]{35Cel}", "m[H2O]{35Cel}", "ucum_code", 1.0, 1.0, None, None),
    ],
)
def test_simple_unit_conversion(
    invocation_tracker,
    source_slot: str,
    target_slot: str,
    source_unit: str,
    target_unit: str,
    unit_metaslot: str,
    source_value: float,
    target_value: Optional[float],
    err: Optional[Exception],
    skip: Optional[str],
) -> None:
    """
    Test unit conversion.

    This test uses a simple source schema with a single class and a single attribute, where the attribute
    is described using the [units](https://w3id.org/linkml/units) metaslot.

    The recommended way to describe unit slots in LinkML is with UCUM, but a number of other schemes
    can be used. We explicitly test for some known cases where UCUM uses non-standard units (e.g. Cel, mo),
    as well as UCUM-specific syntax (e.g. `m.s-1`) and extensions (e.g. using annotations like `{Cre}`).

    :param invocation_tracker: pytest fixture to emit metadata
    :param source_slot: name of slot in source schema
    :param target_slot: name of slot in target schema
    :param source_unit: unit of source slot
    :param target_unit: unit of target slot
    :param source_value: magnitude of source slot (to be converted)
    :param target_value: expected magnitude of target slot (output of conversion)
    :param err:
    :return:
    """
    if skip:
        pytest.skip(f"TODO: {skip}")
    print(
        f"Unit Conversion: `{source_value}` `{source_unit}` => "
        f"`{target_value}` `{target_unit}` [with {source_slot}]\n\n"
    )
    if source_unit == target_unit:
        print("Isomorphic mapping: **input must equal output**")
    classes = {
        "C": {
            "attributes": {
                source_slot: {
                    "range": "float",
                    "unit": {
                        unit_metaslot: source_unit,
                    },
                }
            }
        }
    }
    schema = build_schema("types", classes=classes)
    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "slot_derivations": {
                target_slot: {
                    "populated_from": source_slot,
                    "unit_conversion": {
                        "target_unit": target_unit,
                    },
                }
            }
        }
    }
    spec = build_transformer(class_derivations=cds)

    source_object = {source_slot: source_value}
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={target_slot: target_value} if target_value is not None else None,
        source_sv=source_sv,
        invertible=True,
        raises_error=err,
    )


@pytest.mark.parametrize(
    ("source_unit", "target_unit", "source_value", "target_value", "roundtrip_object", "err"),
    [
        ("m", "cm", 1.0, 100.0, {"q": {"unit": "cm", "magnitude": 100.0}}, None),
        ("cm", "cm", 100.0, 100.0, {"q": {"unit": "cm", "magnitude": 100.0}}, None),
        ("cm", "ml", 100.0, None, None, DimensionalityError),
        ("cm", "pinknoodles", 100.0, None, None, UndefinedUnitError),
    ],
)
def test_complex_unit_conversion(
    invocation_tracker,
    source_unit: str,
    target_unit: str,
    source_value: float,
    target_value: Optional[float],
    roundtrip_object: Optional[dict[str, Any]],
    err: Optional[Exception],
) -> None:
    """
    Test unit conversion, from complex object to simple scalar.

    An example complex object would be an object with separate attributes for
    representing magnitude (value) and unit.

    For example `magnitude: 1.0, unit: "m"`

    :param invocation_tracker:
    :param source_unit: unit of source slot
    :param target_unit: unit of target slot
    :param source_value: magnitude of source slot (to be converted)
    :param target_value: expected magnitude of target slot (output of conversion)
    :param roundtrip_object: expected value of passing target object back through inverted transformation
    :param err: True if expected to raise an Error
    :return:
    """
    target_slot = f"q_in_{target_unit}"
    classes = {
        "Q": {
            "attributes": {
                "magnitude": {
                    "range": "float",
                },
                "unit": {
                    "range": "string",
                },
            },
        },
        "C": {
            "tree_root": True,
            "attributes": {
                "q": {
                    "range": "Q",
                }
            },
        },
    }
    schema = build_schema("types", classes=classes)
    source_sv = SchemaView(schema)
    cds = {
        "D": {
            "populated_from": "C",
            "slot_derivations": {
                target_slot: {
                    "populated_from": "q",
                    "unit_conversion": {
                        "target_unit": target_unit,
                        "source_unit_slot": "unit",
                        "source_magnitude_slot": "magnitude",
                    },
                }
            },
        }
    }
    spec = build_transformer(class_derivations=cds)

    source_object = {
        "q": {
            "magnitude": source_value,
            "unit": source_unit,
        }
    }
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={target_slot: target_value} if target_value is not None else None,
        source_sv=source_sv,
        invertible=True,
        roundtrip_object=roundtrip_object,
        raises_error=err,
    )


@pytest.mark.parametrize(
    ("syntax", "delimiter", "source_value", "target_value"),
    [
        (None, ",", ["a", "b"], "a,b"),
        (None, "|", ["a", "b"], "a|b"),
        (None, "|", ["a"], "a"),
        (None, "|", [], ""),
        (SerializationSyntaxType.JSON, None, ["a", "b"], '["a", "b"]'),
        (SerializationSyntaxType.JSON, None, [], "[]"),
        (SerializationSyntaxType.YAML, None, ["a", "b"], "[a, b]"),
    ],
)
def test_stringify(
    invocation_tracker,
    syntax: Optional[SerializationSyntaxType],
    delimiter: Optional[str],
    source_value: list[str],
    target_value: str,
) -> None:
    """
    Test compaction of multivalued slots into a string.

    Stringification is primarily intended for mapping from complex nested formats to
    simple tabular TSV formats, where some of the following methodologies can be used:

    - flattening lists using an (internal) delimiter
    - flattening lists or more complex objects using JSON or YAML

    For example, `["a", "b"]` => `"a,b"`

    As a convention we use `s1_verbatim` as a slot/attribute name for the
    stringified form.

    :param invocation_tracker: pytest fixture to emit metadata
    :param syntax: SerializationSyntaxType
    :param delimiter: delimiter to use in stringification
    :param source_value: source value (a list)
    :param target_value: expected value of slot in target object (a string)
    :return:
    """
    classes = {
        "C": {
            "attributes": {
                "s1": {"range": "string", "multivalued": True},
            }
        },
    }
    schema = build_schema("types", classes=classes)
    source_sv = SchemaView(schema)
    cds = {
        "D": {
            "populated_from": "C",
            "slot_derivations": {
                "s1_verbatim": {
                    "populated_from": "s1",
                    "stringification": {
                        "syntax": syntax,
                        "delimiter": delimiter,
                    },
                }
            },
        }
    }
    spec = build_transformer(class_derivations=cds)
    source_object = {"s1": source_value}
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={"s1_verbatim": target_value},
        source_sv=source_sv,
        invertible=True,
    )
    create_compilers(spec, {SQLCompiler: ""})


@pytest.mark.parametrize(
    "source_object",
    [
        ({"c_list": [{"s1": "a", "s2": "b"}, {"s1": "c", "s2": "d"}], "d": {"s3": "e"}}),
    ],
)
@pytest.mark.parametrize("use_expr", [True, False])
@pytest.mark.parametrize("supply_source_schema", [True])  # TODO
def test_isomorphic(
    invocation_tracker,
    source_object: dict[str, Any],
    use_expr: bool,  # noqa: FBT001
    supply_source_schema: bool,  # noqa: FBT001
) -> None:
    """
    Test mapping a schema to an identical schema (i.e copy).

    This also tests for the ability to recursively descend a nested structure.

    :param invocation_tracker:
    :param source_object:
    :param use_expr:
    :param supply_source_schema: TODO: always True for now
    :return:
    """
    classes = {
        "Container": {
            "tree_root": True,
            "attributes": {
                "c_list": {
                    "range": "C",
                    "multivalued": True,
                },
                "d": {
                    "range": "D",
                },
            },
        },
        "C": {
            "attributes": {
                "s1": {
                    "range": "string",
                },
                "s2": {
                    "range": "string",
                },
            }
        },
        "D": {
            "attributes": {
                "s3": {
                    "range": "string",
                },
            },
        },
    }
    schema = build_schema("isomorphic", classes=classes)
    source_sv = SchemaView(schema)
    mapping_key = "expr" if use_expr else "populated_from"
    cds = {
        "Container": {
            "populated_from": "Container",
            "slot_derivations": {
                "c_list": {
                    "populated_from": "c_list",
                    "range": "C",
                },
                "d": {
                    "populated_from": "d",
                    "range": "D",
                },
            },
        },
        "C": {
            "populated_from": "C",
            "slot_derivations": {
                "s1": {
                    "populated_from": "s1",
                },
                "s2": {
                    "populated_from": "s2",
                },
            },
        },
        "D": {
            "populated_from": "D",
            "slot_derivations": {
                "s3": {
                    mapping_key: "s3",
                }
            },
        },
    }
    spec = build_transformer(class_derivations=cds)
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object=source_object,
        source_sv=source_sv,
        invertible=True,
        supply_source_schema=supply_source_schema,
    )


@pytest.mark.parametrize("inlined", [True, False])
@pytest.mark.parametrize(
    ("source_object", "target_object"),
    [
        (
            {"s1": {"id": "x1", "name": "foo"}, "s2": {"id": "x2", "name": "bar"}},
            {"s1_id": "x1", "s1_name": "foo", "s2_id": "x2", "s2_name": "bar"},
        ),
    ],
)
def test_join(
    invocation_tracker,
    source_object: dict[str, Any],
    target_object: dict[str, Any],
    inlined: bool,  # noqa: FBT001
) -> None:
    """
    Test joining two objects into a single object, aka denormalization.

    :param invocation_tracker:
    :param source_object: normalized source object
    :param target_object: denormalized target object
    :param inlined: True if the source objects are inlined
    :return:
    """
    classes = {
        "R": {
            "tree_root": inlined,
            "attributes": {
                "s1": {
                    "range": "E",
                    "inlined": inlined,
                },
                "s2": {
                    "range": "E",
                    "inlined": inlined,
                },
            },
        },
        "E": {
            "attributes": {
                "id": {
                    "range": "string",
                    "identifier": True,
                },
                "name": {
                    "range": "string",
                },
            },
        },
    }
    cds = {
        "R": {
            "populated_from": "R",
            "slot_derivations": {
                "s1_id": {
                    "expr": "s1.id",
                },
                "s1_name": {
                    "expr": "s1.name",
                },
                "s2_id": {
                    "expr": "s2.id",
                },
                "s2_name": {
                    "expr": "s2.name",
                },
            },
        },
    }
    if not inlined:
        classes["Container"] = {
            "tree_root": True,
            "attributes": {
                "r_list": {
                    "range": "R",
                    "multivalued": True,
                },
                "e_list": {
                    "range": "E",
                    "multivalued": True,
                    "inlined_as_list": True,
                },
            },
        }
        source_object = {
            "r_list": [{"s1": source_object["s1"]["id"], "s2": source_object["s2"]["id"]}],
            "e_list": [source_object["s1"], source_object["s2"]],
        }
        target_object = {"r_list": [target_object]}
        cds["Container"] = {
            "populated_from": "Container",
            "slot_derivations": {
                "r_list": {
                    "populated_from": "r_list",
                },
            },
        }
    schema = build_schema("types", classes=classes)
    source_sv = SchemaView(schema)

    spec = build_transformer(class_derivations=cds)
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object=target_object,
        source_sv=source_sv,
        invertible=False,
        index=not inlined,
    )


@pytest.mark.parametrize(
    ("source_value", "mapping", "target_value", "mirror_source"),
    [
        ("A", {"B": "A"}, "B", False),
        ("Z", {"B": "A"}, None, False),
        ("C", {"B": "A"}, "C", True),
        ("A", {"B": ["A", "C"]}, "B", False),
        ("C", {"B": ["A", "C"]}, "B", False),
    ],
)
def test_map_enum(
    invocation_tracker,
    source_value: str,
    mapping: dict[str, Any],
    target_value: Optional[str],
    mirror_source: bool,  # noqa: FBT001
) -> None:
    """
    Test mapping between enum values.

    Currently this only supports simple dictionary-style mapping between permissible values,
    akin to SSSOM, but in future additional expressivity will be supported, including:

    - mapping ranges to categorical values
    - boolean/branching logic

    :param invocation_tracker:
    :param source_value: source enum permissible value to be mapped
    :param mapping: mapping from source to target enum permissible values
    :param target_value: expected target enum permissible value
    :return:
    """
    classes = {
        "C": {
            "attributes": {
                "s1": {
                    "range": "E",
                }
            }
        }
    }
    enums = {"E": {"permissible_values": ["A", "B", "C"]}}
    schema = build_schema("enums", classes=classes, enums=enums)
    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "slot_derivations": {
                "s1": {
                    "populated_from": "s1",
                }
            }
        }
    }
    pv_derivs = {}
    invertible = True
    for k, v in mapping.items():
        if isinstance(v, list):
            pv_derivs[k] = {"sources": v}
            invertible = False
        else:
            pv_derivs[k] = {"populated_from": v}

    eds = {
        "E": {
            "populated_from": "E",
            "mirror_source": mirror_source,
            "permissible_value_derivations": pv_derivs,
        },
    }
    spec = build_transformer(class_derivations=cds, enum_derivations=eds)
    source_object = {"s1": source_value}
    if target_value is None:
        invertible = False
    if mirror_source:
        pytest.skip("TODO: mirror_source")
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object={"s1": target_value},
        source_sv=source_sv,
        invertible=invertible,
    )


@pytest.mark.parametrize("is_a", [True, False])
@pytest.mark.parametrize("flatten", [False, True])
def test_inheritance(invocation_tracker, is_a: bool, flatten: bool) -> None:  # noqa: FBT001
    """
    Test inheritance.

    Transformation specifications can utilize inheritance, in the same way that LinkML schemas can.

    :param invocation_tracker: pytest fixture to emit metadata
    :param is_a: use is_as instead of mixins in test schema
    :param flatten: roll down inherited slots
    :return:
    """
    classes = {
        "C": {
            "tree_root": True,
            "attributes": {
                "s1": {
                    "range": "integer",
                }
            },
        },
        "D": {
            "attributes": {
                "s2": {
                    "range": "integer",
                }
            },
        },
    }
    if is_a:
        classes["C"]["is_a"] = "D"
    else:
        classes["C"]["mixins"] = ["D"]

    schema = build_schema("expr", classes=classes)

    source_sv = SchemaView(schema)
    cds = {
        "C": {
            "populated_from": "C",
            "slot_derivations": {
                "s1": {
                    "expr": "s1 + 1",
                },
            },
        },
        "D": {
            "populated_from": "D",
            "slot_derivations": {
                "s2": {
                    "expr": "s2 + 1",
                }
            },
        },
    }
    if flatten:
        cds["C"]["slot_derivations"]["s2"] = {
            "expr": "s2 + 1",
        }
        del cds["D"]
    elif is_a:
        cds["C"]["is_a"] = "D"
    else:
        cds["C"]["mixins"] = ["D"]
    spec = build_transformer(class_derivations=cds)
    source_object = {"s1": 1, "s2": 2}
    target_object = {"s1": 2, "s2": 3}
    map_object(
        spec=spec,
        source_object=source_object,
        expected_target_object=target_object,
        source_sv=source_sv,
        invertible=False,
    )
