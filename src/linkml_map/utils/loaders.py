from pathlib import Path
from typing import Union

import yaml
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview
from linkml_runtime.loaders import yaml_loader, json_loader, csv_loader, tsv_loader, rdf_loader, rdflib_loader

from linkml_map.datamodel.transformer_model import TransformationSpecification
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


def load_specification(path: Union[Path, str]) -> TransformationSpecification:
    if isinstance(path, Path):
        path = str(path)
    with open(path) as f:
        obj = yaml.safe_load(f)
        # necessary to expand first
        normalizer = ReferenceValidator(
            package_schemaview("linkml_map.datamodel.transformer_model")
        )
        normalizer.expand_all = True
        obj = normalizer.normalize(obj)
        return TransformationSpecification(**obj)


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


def load_file_as_dict(file_path) -> dict:
    suffix = Path(file_path).suffix.lower()

    loader = get_loader_by_suffix(suffix)

    if not loader:
        raise ValueError(f"No loader found for file extension: {suffix}")

    return loader.load_as_dict(file_path)