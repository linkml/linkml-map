"""Tests for pre-flight spec validation in CLI commands.

The map-data, compile, invert, and derive-schema commands run the validator
on the loaded spec before performing their action. Findings (deprecation
warnings, reference resolution errors) are surfaced to stderr but never
gate execution — runtime remains the authoritative arbiter. Users who
want fail-fast behavior should run ``validate-spec --strict`` separately.
"""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from linkml_map.cli.cli import main

SOURCE_SCHEMA = """\
id: https://example.org/source
name: source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Person:
    attributes:
      name:
        range: string
      given_name:
        range: string
      family_name:
        range: string
"""


@pytest.fixture
def runner() -> CliRunner:
    """CliRunner with stderr captured separately for pre-flight assertions."""
    return CliRunner()


@pytest.fixture
def source_schema(tmp_path: Path) -> Path:
    p = tmp_path / "source.yaml"
    p.write_text(SOURCE_SCHEMA)
    return p


@pytest.fixture
def deprecated_spec(tmp_path: Path) -> Path:
    """A spec that uses the deprecated ``sources`` field."""
    spec = {
        "id": "https://example.org/transform",
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "sources": ["LegacyPerson"],
                "slot_derivations": {"name": {"populated_from": "name"}},
            },
        },
    }
    p = tmp_path / "transform.yaml"
    p.write_text(yaml.safe_dump(spec))
    return p


@pytest.fixture
def deprecated_data(tmp_path: Path) -> Path:
    """Minimal input data for the deprecated_spec transform."""
    p = tmp_path / "data.yaml"
    p.write_text(yaml.safe_dump({"name": "Alice"}))
    return p


def test_map_data_pre_flight_surfaces_deprecation_to_stderr(
    runner: CliRunner,
    source_schema: Path,
    deprecated_spec: Path,
    deprecated_data: Path,
) -> None:
    """``map-data`` prints deprecation messages to stderr but still runs."""
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(deprecated_spec),
            "-s",
            str(source_schema),
            "--source-type",
            "Person",
            str(deprecated_data),
        ],
    )
    assert result.exit_code == 0, result.output
    # Deprecation message routed through click.echo(err=True). When stderr is
    # not separated (default CliRunner), it appears in result.output.
    combined = (result.output or "") + (result.stderr_bytes or b"").decode()
    assert "sources" in combined
    assert "deprecated" in combined.lower()


def test_pre_flight_does_not_gate_on_validation_findings(
    runner: CliRunner,
    source_schema: Path,
    deprecated_data: Path,
    tmp_path: Path,
) -> None:
    """Pre-flight surfaces findings but never aborts the command itself.

    A spec referencing a class that doesn't exist in the source schema
    produces an error-severity validation message, but ``map-data`` still
    runs (the runtime will fail informatively later if the broken path is
    actually exercised).
    """
    spec = {
        "id": "https://example.org/transform",
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {"name": {"populated_from": "name"}},
            },
            # Orphan derivation referencing a class that doesn't exist —
            # validator will flag as error, runtime will skip (no Mapping
            # instances in input data).
            "Orphan": {
                "populated_from": "DoesNotExist",
            },
        },
    }
    spec_path = tmp_path / "spec_with_orphan.yaml"
    spec_path.write_text(yaml.safe_dump(spec))

    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(spec_path),
            "-s",
            str(source_schema),
            "--source-type",
            "Person",
            str(deprecated_data),
        ],
    )
    assert result.exit_code == 0, result.output


def test_compile_pre_flight_surfaces_deprecation(
    runner: CliRunner,
    source_schema: Path,
    deprecated_spec: Path,
) -> None:
    """``compile`` runs the pre-flight pass before compiling."""
    result = runner.invoke(
        main,
        [
            "compile",
            "-T",
            str(deprecated_spec),
            "-s",
            str(source_schema),
            "--target",
            "python",
        ],
    )
    assert result.exit_code == 0, result.output
    combined = (result.output or "") + (result.stderr_bytes or b"").decode()
    assert "sources" in combined
    assert "deprecated" in combined.lower()


def test_clean_spec_emits_no_pre_flight_output(
    runner: CliRunner,
    source_schema: Path,
    deprecated_data: Path,
    tmp_path: Path,
) -> None:
    """A spec without deprecated fields or reference issues is silent."""
    spec = {
        "id": "https://example.org/transform",
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {"name": {"populated_from": "name"}},
            },
        },
    }
    spec_path = tmp_path / "clean.yaml"
    spec_path.write_text(yaml.safe_dump(spec))

    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(spec_path),
            "-s",
            str(source_schema),
            "--source-type",
            "Person",
            str(deprecated_data),
        ],
    )
    assert result.exit_code == 0, result.output
    combined = (result.output or "") + (result.stderr_bytes or b"").decode()
    # No pre-flight findings should appear; stdout will contain transform
    # output but no deprecation-style messages.
    assert "[warning]" not in combined
    assert "[error]" not in combined
