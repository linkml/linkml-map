"""
Utility functions for automatic selection of loaders and dumpers based on file extension.
This module provides convenience functions for working with LinkML data files.
"""

from pathlib import Path
from typing import Union, Optional, Any, Dict, List, Type

from pydantic import BaseModel
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_runtime.loaders import (
    yaml_loader, json_loader, csv_loader, tsv_loader, rdf_loader, rdflib_loader
)
from linkml_runtime.dumpers import (
    yaml_dumper, json_dumper, csv_dumper, tsv_dumper, rdf_dumper, rdflib_dumper
)

from linkml_map.utils.file_formats import FileFormat


# Mapping from FileFormat to loaders
FORMAT_LOADER_MAP = {
    FileFormat.YAML: yaml_loader,
    FileFormat.JSON: json_loader,
    FileFormat.CSV: csv_loader,
    FileFormat.TSV: tsv_loader,
    FileFormat.RDF: rdf_loader,
    FileFormat.TTL: rdf_loader,
    FileFormat.OWL: rdf_loader,
    FileFormat.JSONLD: rdflib_loader
}

# Mapping from FileFormat to dumpers
FORMAT_DUMPER_MAP = {
    FileFormat.YAML: yaml_dumper,
    FileFormat.JSON: json_dumper,
    FileFormat.CSV: csv_dumper,
    FileFormat.TSV: tsv_dumper,
    FileFormat.RDF: rdf_dumper,
    FileFormat.TTL: rdf_dumper,
    FileFormat.OWL: rdf_dumper,
    FileFormat.JSONLD: rdflib_dumper
}


def get_loader_by_suffix(suffix: str):
    """
    Get the appropriate loader based on file suffix
    
    Args:
        suffix: File suffix (e.g., '.yaml', '.json')
        
    Returns:
        The appropriate loader for the given suffix
        
    Raises:
        ValueError: If the suffix is not supported
    """
    file_format = FileFormat.from_suffix(suffix)
    return FORMAT_LOADER_MAP[file_format]


def get_dumper_by_suffix(suffix: str):
    """
    Get the appropriate dumper based on file suffix
    
    Args:
        suffix: File suffix (e.g., '.yaml', '.json')
        
    Returns:
        The appropriate dumper for the given suffix
        
    Raises:
        ValueError: If the suffix is not supported
    """
    file_format = FileFormat.from_suffix(suffix)
    return FORMAT_DUMPER_MAP[file_format]



def dump_file(data: Union[BaseModel, YAMLRoot, Dict, List], file_path: Union[str, Path], **kwargs) -> None:
    """
    Dump data to a file using the appropriate dumper based on file extension
    
    Args:
        data: Data to dump
        file_path: Path to the file to write
        **kwargs: Additional arguments to pass to the dumper
    """
    file_path = Path(file_path)
    dumper = get_dumper_by_suffix(file_path.suffix)
    
    dumper.dump(data, str(file_path), **kwargs)


def dumps(data: Union[BaseModel, YAMLRoot, Dict, List], format_or_suffix: Union[str, FileFormat], **kwargs) -> str:
    """
    Dump data to a string using the appropriate dumper based on suffix
    
    Args:
        data: Data to dump
        format_or_suffix: Either a FileFormat enum or a file suffix to determine the format (e.g., '.yaml', '.json')
        **kwargs: Additional arguments to pass to the dumper
        
    Returns:
        String representation of the data in the specified format
    """
    if isinstance(format_or_suffix, FileFormat):
        # Use the FileFormat directly to get the format-specific dumper
        dumper = FORMAT_DUMPER_MAP[format_or_suffix]
    else:
        # Treat as a suffix and get the appropriate dumper
        dumper = get_dumper_by_suffix(format_or_suffix)
    return dumper.dumps(data, **kwargs)