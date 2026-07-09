"""Generalized data loader for linkml-map supporting multiple file formats."""

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime import SchemaView


class FileFormat(str, Enum):
    """Supported file formats for data loading."""

    YAML = "yaml"
    JSON = "json"
    TSV = "tsv"
    CSV = "csv"

    @classmethod
    def from_extension(cls, path: str | Path) -> "FileFormat":
        """Determine file format from file extension."""
        ext = Path(path).suffix.lower()
        mapping = {
            ".yaml": cls.YAML,
            ".yml": cls.YAML,
            ".json": cls.JSON,
            ".tsv": cls.TSV,
            ".csv": cls.CSV,
        }
        if ext not in mapping:
            msg = f"Unsupported file extension: {ext}"
            raise ValueError(msg)
        return mapping[ext]


_NUMERIC_TYPE_NAMES = frozenset({"integer", "float", "double", "decimal"})


def _numeric_slots_for(schemaview: SchemaView, target_class: str) -> set[str]:
    """
    Return the names of ``target_class`` slots whose range is a numeric type.

    Mirrors the numeric-slot detection in linkml's delimited loader, but operates
    on an already-built :class:`SchemaView` so the source schema is parsed once for
    the whole run instead of being rebuilt from disk per file. Rebuilding per file
    is both slow and leaky on large generated schemas. See linkml/linkml-map#283.

    :param schemaview: Source schema, built once and reused across files.
    :param target_class: Source class the file's rows conform to.
    :return: Slot names (and aliases) whose range resolves to a numeric type.
    """
    numeric: set[str] = set()
    all_types = schemaview.all_types()
    for slot in schemaview.class_induced_slots(target_class):
        if slot.range in all_types and any(
            ancestor in _NUMERIC_TYPE_NAMES for ancestor in schemaview.type_ancestors(slot.range)
        ):
            numeric.add(slot.name)
            if slot.alias:
                numeric.add(slot.alias)
    return numeric


def _apply_numeric_slots(loader: Any, schemaview: SchemaView | None, target_class: str | None) -> None:
    """
    Configure schema-aware numeric coercion on a linkml delimited loader.

    Assigns the numeric-slot set (computed from the in-scope, already-built
    :class:`SchemaView`) to the loader so it coerces only numeric-ranged columns,
    without linkml rebuilding a ``SchemaView`` per file. When no schema/class is
    available the loader keeps its default (coerce every numeric-looking value).
    See linkml/linkml-map#283.

    ``_numeric_slots`` is linkml's own hook for this; the durable fix is upstream
    support for handing the loader a ready-made ``SchemaView`` (linkml/linkml#3610).
    """
    if schemaview is not None and target_class is not None:
        loader._numeric_slots = _numeric_slots_for(schemaview, target_class)


class BaseFileLoader(ABC):
    """Abstract base class for file loaders."""

    def __init__(self, source: str | Path) -> None:
        """Initialize with a file path."""
        self.source = Path(source)
        if not self.source.exists():
            msg = f"File not found: {self.source}"
            raise FileNotFoundError(msg)

    @abstractmethod
    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Iterate over data instances from the file."""


class YamlFileLoader(BaseFileLoader):
    """Loader for YAML files."""

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Load and yield the YAML content as a single instance."""
        with open(self.source) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            yield from data
        else:
            yield data


class JsonFileLoader(BaseFileLoader):
    """Loader for JSON files."""

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Load and yield the JSON content."""
        with open(self.source) as f:
            data = json.load(f)
        if isinstance(data, list):
            yield from data
        else:
            yield data


class TsvFileLoader(BaseFileLoader):
    """Loader for TSV files using linkml's TsvLoader."""

    def __init__(
        self,
        source: str | Path,
        skip_empty_rows: bool = True,
        schemaview: SchemaView | None = None,
        target_class: str | None = None,
    ) -> None:
        """Initialize TSV loader."""
        super().__init__(source)
        self.skip_empty_rows = skip_empty_rows
        self.schemaview = schemaview
        self.target_class = target_class

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Iterate over rows from the TSV file."""
        from linkml.validator.loaders import TsvLoader

        loader = TsvLoader(str(self.source), skip_empty_rows=self.skip_empty_rows)
        _apply_numeric_slots(loader, self.schemaview, self.target_class)
        yield from loader.iter_instances()


class CsvFileLoader(BaseFileLoader):
    """Loader for CSV files using linkml's CsvLoader."""

    def __init__(
        self,
        source: str | Path,
        skip_empty_rows: bool = True,
        schemaview: SchemaView | None = None,
        target_class: str | None = None,
    ) -> None:
        """Initialize CSV loader."""
        super().__init__(source)
        self.skip_empty_rows = skip_empty_rows
        self.schemaview = schemaview
        self.target_class = target_class

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Iterate over rows from the CSV file."""
        from linkml.validator.loaders import CsvLoader

        loader = CsvLoader(str(self.source), skip_empty_rows=self.skip_empty_rows)
        _apply_numeric_slots(loader, self.schemaview, self.target_class)
        yield from loader.iter_instances()


def get_file_loader(
    path: str | Path,
    file_format: FileFormat | None = None,
    **kwargs: Any,
) -> BaseFileLoader:
    """
    Get the appropriate file loader for a given path.

    :param path: Path to the file
    :param file_format: Explicit file format (auto-detected from extension if not provided)
    :param kwargs: Additional arguments passed to the loader
    :return: Appropriate file loader instance
    """
    if file_format is None:
        file_format = FileFormat.from_extension(path)

    loader_map: dict[FileFormat, type[BaseFileLoader]] = {
        FileFormat.YAML: YamlFileLoader,
        FileFormat.JSON: JsonFileLoader,
        FileFormat.TSV: TsvFileLoader,
        FileFormat.CSV: CsvFileLoader,
    }

    loader_class = loader_map.get(file_format)
    if loader_class is None:
        msg = f"No loader available for format: {file_format}"
        raise ValueError(msg)

    return loader_class(path, **kwargs)


class DataLoader:
    """
    Load data files from a directory based on identifiers.

    This class supports loading data from multiple files in a directory,
    where each file corresponds to a `populated_from` identifier in the
    transformation specification.

    Supports YAML, JSON, TSV, and CSV file formats, with auto-detection
    based on file extension.

    Example usage:
        # Directory-based loading (for multi-file transforms)
        loader = DataLoader("/path/to/data")
        for row in loader["Person"]:  # Loads Person.tsv, Person.csv, etc.
            process(row)

        # Single-file loading
        loader = DataLoader("/path/to/data/people.tsv")
        for row in loader:
            process(row)
    """

    def __init__(
        self,
        base_path: str | Path,
        default_format: FileFormat | None = None,
        skip_empty_rows: bool = True,
        schemaview: SchemaView | None = None,
    ) -> None:
        """
        Initialize the data loader.

        :param base_path: Base directory containing data files, or a single file path
        :param default_format: Default format to use when extension is ambiguous
        :param skip_empty_rows: Skip empty rows in tabular files (default: True)
        :param schemaview: Source schema (enables schema-aware type coercion for TSV/CSV).
            The target class is derived from each file's identifier.
        :raises FileNotFoundError: If the path does not exist
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            msg = f"Path not found: {self.base_path}"
            raise FileNotFoundError(msg)
        self.default_format = default_format
        self.skip_empty_rows = skip_empty_rows
        self.schemaview = schemaview

    def _schema_loader_kwargs(self, identifier: str) -> dict[str, Any]:
        """
        Build schema-aware kwargs for a TSV/CSV leaf loader.

        Passes the in-scope :class:`SchemaView` (built once) straight through to the
        leaf loader, so numeric-slot detection reuses it rather than rebuilding a
        ``SchemaView`` from disk per file (slow and memory-leaky on large generated
        schemas). See linkml/linkml-map#283.

        :param identifier: Names the source class the file's rows conform to.
        :return: ``schemaview``/``target_class`` kwargs, or empty if no schema is
            available (rows then coerce every numeric-looking value, as before).
        """
        if self.schemaview is None:
            return {}
        return {"schemaview": self.schemaview, "target_class": identifier}

    @property
    def is_single_file(self) -> bool:
        """Check if loader is configured for single-file mode."""
        return self.base_path.is_file()

    def iter_sources(self) -> Iterator[tuple[str, Iterator[dict[str, Any]]]]:
        """
        Iterate over all data sources, yielding (identifier, rows) pairs.

        This provides a unified interface for both single-file and directory modes.
        For single files, the identifier is the file stem.
        For directories, each file's stem is used as its identifier.

        :yield: Tuples of (identifier, row_iterator)
        """
        if self.is_single_file:
            identifier = self.base_path.stem
            yield identifier, iter(self)
        else:
            for identifier in self.get_available_identifiers():
                yield identifier, self[identifier]

    def _find_file(self, identifier: str) -> Path | None:
        """
        Find a data file matching the identifier.

        Searches for files with supported extensions in order of preference.
        """
        if not self.base_path.is_dir():
            msg = "Cannot search for files when loader is in single-file mode."
            raise ValueError(msg)

        # Search order: prefer explicit format, then TSV, CSV, YAML, JSON
        if self.default_format:
            extensions = [f".{self.default_format.value}"]
        else:
            extensions = [".tsv", ".csv", ".yaml", ".yml", ".json"]

        for ext in extensions:
            file_path = self.base_path / f"{identifier}{ext}"
            if file_path.exists():
                return file_path

        return None

    def get_path(self, identifier: str) -> Path:
        """
        Return the resolved file path for *identifier*.

        :param identifier: Logical table/file name (without extension).
        :returns: Absolute path to the matching data file.
        :raises FileNotFoundError: If no matching file is found.
        """
        path = self._find_file(identifier)
        if path is None:
            msg = f"No data file found for identifier {identifier!r} under {self.base_path}"
            raise FileNotFoundError(msg)
        return path.resolve()

    def __contains__(self, identifier: str) -> bool:
        """Check if a data file exists for the given identifier."""
        if self.is_single_file:
            return identifier == self.base_path.stem
        return self._find_file(identifier) is not None

    def __getitem__(self, identifier: str) -> Iterator[dict[str, Any]]:
        """
        Load instances from the data file corresponding to the identifier.

        For single-file mode, the identifier must match the file stem.

        :param identifier: The populated_from identifier to load
        :return: Iterator over data instances
        :raises FileNotFoundError: If no matching file is found
        """
        if self.is_single_file:
            if identifier == self.base_path.stem:
                return iter(self)
            msg = f"Single-file loader has no data for identifier '{identifier}' (file stem is '{self.base_path.stem}')"
            raise FileNotFoundError(msg)

        file_path = self._find_file(identifier)
        if file_path is None:
            msg = f"No data file found for identifier '{identifier}' in {self.base_path}"
            raise FileNotFoundError(msg)

        loader_kwargs = {}
        file_format = FileFormat.from_extension(file_path)
        if file_format in (FileFormat.TSV, FileFormat.CSV):
            loader_kwargs["skip_empty_rows"] = self.skip_empty_rows
            loader_kwargs.update(self._schema_loader_kwargs(identifier))

        loader = get_file_loader(file_path, **loader_kwargs)
        return loader.iter_instances()

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over instances when using single-file mode."""
        if not self.is_single_file:
            msg = "Cannot iterate directly on directory-based loader. Use loader[identifier] instead."
            raise ValueError(msg)

        loader_kwargs = {}
        file_format = FileFormat.from_extension(self.base_path)
        if file_format in (FileFormat.TSV, FileFormat.CSV):
            loader_kwargs["skip_empty_rows"] = self.skip_empty_rows
            # Single-file mode: the file stem names the source class.
            loader_kwargs.update(self._schema_loader_kwargs(self.base_path.stem))

        loader = get_file_loader(self.base_path, **loader_kwargs)
        yield from loader.iter_instances()

    def get_available_identifiers(self) -> list[str]:
        """
        Get list of available data file identifiers in the directory.

        :return: List of identifiers (file stems) for supported file types
        """
        if self.is_single_file:
            return []

        identifiers = set()
        supported_extensions = {".tsv", ".csv", ".yaml", ".yml", ".json"}

        for file_path in self.base_path.iterdir():
            if file_path.suffix.lower() in supported_extensions:
                identifiers.add(file_path.stem)

        return sorted(identifiers)

    def load_all(self) -> dict[str, list[dict[str, Any]]]:
        """
        Load all available data files.

        :return: Dictionary mapping identifiers to lists of instances
        """
        if self.is_single_file:
            return {"_single": list(self)}

        result = {}
        for identifier in self.get_available_identifiers():
            result[identifier] = list(self[identifier])
        return result


def load_data_file(
    path: str | Path,
    file_format: FileFormat | None = None,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """
    Convenience function to load data from a single file.

    :param path: Path to the data file
    :param file_format: Explicit file format (auto-detected if not provided)
    :param kwargs: Additional arguments passed to the loader
    :return: Iterator over data instances
    """
    loader = get_file_loader(path, file_format, **kwargs)
    return loader.iter_instances()
