"""
Common format definitions and utilities for file I/O operations.
"""

from enum import Enum
from typing import Dict, Any, Optional, List


class FileFormat(Enum):
    """Enumeration of supported file formats."""
    YAML = "yaml"
    JSON = "json"
    CSV = "csv"
    TSV = "tsv"
    RDF = "rdf"
    TTL = "ttl"
    OWL = "owl"
    JSONLD = "jsonld"
    
    @classmethod
    def from_suffix(cls, suffix: str) -> 'FileFormat':
        """
        Get the FileFormat enum from a file suffix.
        
        Args:
            suffix: File suffix (e.g., '.yaml', '.json')
            
        Returns:
            The corresponding FileFormat enum
            
        Raises:
            ValueError: If the suffix is not supported
        """
        suffix = suffix.lower()
        if suffix.startswith('.'):
            suffix = suffix[1:]
            
        suffix_map = {
            'yaml': cls.YAML,
            'yml': cls.YAML,
            'json': cls.JSON,
            'csv': cls.CSV,
            'tsv': cls.TSV,
            'rdf': cls.RDF,
            'ttl': cls.TTL,
            'owl': cls.OWL,
            'jsonld': cls.JSONLD
        }
        
        if suffix not in suffix_map:
            raise ValueError(f"Unsupported file extension: {suffix}")
            
        return suffix_map[suffix]
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """
        Get all format values as strings.
        
        Returns:
            List of all format values
        """
        return [fmt.value for fmt in cls]


# Format option string for CLI help
FORMAT_OPTION_STRING = ", ".join(FileFormat.get_all_values())