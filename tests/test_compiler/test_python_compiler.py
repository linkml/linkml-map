"""
Tests compilation of a specification to python
"""

import pytest
from linkml_runtime import SchemaView
from linkml_runtime.utils.compile_python import compile_python

import tests.input.examples.personinfo_basic.model.personinfo_model as src
from linkml_transformer.compiler.python_compiler import PythonCompiler
from linkml_transformer.utils.loaders import load_specification
from tests import SCHEMA1, SPECIFICATION


@pytest.fixture
def compiler():
    return PythonCompiler(
        source_schemaview=SchemaView(SCHEMA1),
        source_python_module="tests.input.examples.personinfo_basic.model.personinfo_model",
        target_python_module="tests.input.examples.personinfo_basic.model.agent_model",
    )


def test_compile(compiler):
    spec = load_specification(SPECIFICATION)
    pycode = compiler.compile(spec)
    # TODO: include imports so that code compiles
    print(pycode.serialization)
    mod = compile_python(pycode.serialization)
    person = src.Person(
        id="http://example.org/person/1",
        name="Name McNameface",
        age_in_years=23,
    )
    agent = mod.derive_Agent(person)
    print(agent)
    assert agent.id == person.id
    assert agent.label == person.name
    assert agent.age == "23 years"
