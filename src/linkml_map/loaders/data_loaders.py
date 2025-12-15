"""Generalized data loader for linkml-map supporting multiple file formats."""

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import yaml


class FileFormat(str, Enum):
    """Supported file formats for data loading."""

    YAML = "yaml"
    JSON = "json"
    TSV = "tsv"
    CSV = "csv"

    @classmethod
    def from_extension(cls, path: Union[str, Path]) -> "FileFormat":
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


class BaseFileLoader(ABC):
    """Abstract base class for file loaders."""

    def __init__(self, source: Union[str, Path]) -> None:
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
        source: Union[str, Path],
        skip_empty_rows: bool = True,
    ) -> None:
        """Initialize TSV loader."""
        super().__init__(source)
        self.skip_empty_rows = skip_empty_rows

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Iterate over rows from the TSV file."""
        from linkml.validator.loaders import TsvLoader

        loader = TsvLoader(str(self.source), skip_empty_rows=self.skip_empty_rows)
        yield from loader.iter_instances()


class CsvFileLoader(BaseFileLoader):
    """Loader for CSV files using linkml's CsvLoader."""

    def __init__(
        self,
        source: Union[str, Path],
        skip_empty_rows: bool = True,
    ) -> None:
        """Initialize CSV loader."""
        super().__init__(source)
        self.skip_empty_rows = skip_empty_rows

    def iter_instances(self) -> Iterator[dict[str, Any]]:
        """Iterate over rows from the CSV file."""
        from linkml.validator.loaders import CsvLoader

        loader = CsvLoader(str(self.source), skip_empty_rows=self.skip_empty_rows)
        yield from loader.iter_instances()


def get_file_loader(
    path: Union[str, Path],
    file_format: Optional[FileFormat] = None,
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
        base_path: Union[str, Path],
        default_format: Optional[FileFormat] = None,
        skip_empty_rows: bool = True,
    ) -> None:
        """
        Initialize the data loader.

        :param base_path: Base directory containing data files, or a single file path
        :param default_format: Default format to use when extension is ambiguous
        :param skip_empty_rows: Skip empty rows in tabular files (default: True)
        :raises FileNotFoundError: If the path does not exist
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            msg = f"Path not found: {self.base_path}"
            raise FileNotFoundError(msg)
        self.default_format = default_format
        self.skip_empty_rows = skip_empty_rows

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

    def _find_file(self, identifier: str) -> Optional[Path]:
        """
        Find a data file matching the identifier.

        Searches for files with supported extensions in order of preference.
        """
        if not self.base_path.is_dir():
            msg = f"Base path is not a directory: {self.base_path}"
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

    def __contains__(self, identifier: str) -> bool:
        """Check if a data file exists for the given identifier."""
        if self.is_single_file:
            return False
        return self._find_file(identifier) is not None

    def __getitem__(self, identifier: str) -> Iterator[dict[str, Any]]:
        """
        Load instances from the data file corresponding to the identifier.

        :param identifier: The populated_from identifier to load
        :return: Iterator over data instances
        :raises FileNotFoundError: If no matching file is found
        """
        if self.is_single_file:
            msg = "Cannot use identifier-based access on single-file loader"
            raise ValueError(msg)

        file_path = self._find_file(identifier)
        if file_path is None:
            msg = f"No data file found for identifier '{identifier}' in {self.base_path}"
            raise FileNotFoundError(msg)

        loader_kwargs = {}
        file_format = FileFormat.from_extension(file_path)
        if file_format in (FileFormat.TSV, FileFormat.CSV):
            loader_kwargs["skip_empty_rows"] = self.skip_empty_rows

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
    path: Union[str, Path],
    file_format: Optional[FileFormat] = None,
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
