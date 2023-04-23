"""Iterate through all examples in a folder testing them for validity.

"""
import glob
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Union, Any, Mapping, Optional, List, TextIO

import click
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper, rdflib_dumper, yaml_dumper
from linkml_runtime.linkml_model import ElementName
from linkml_runtime.utils.formatutils import camelcase
from pydantic import BaseModel

from linkml_transformer.transformer.object_transformer import ObjectTransformer


class Step(BaseModel):
    source_data: str
    target_data: Optional[str] = None

class Transformation(BaseModel):
    description: Optional[str] = None
    source_schema: str
    transformation_specification: str
    steps: List[Step] = None

class Instructions(BaseModel):
    description: Optional[str] = None
    transformations: List[Transformation] = []



@dataclass
class MultiFileTransformer:
    """
    Processes a collection of inputs in one folder.

    Assumes folder structures:

       - {package}
          - source/{source_schema}.yaml  :: the schema to transform from
          - transform/{transform_spec}.transform.yaml :: mapping spec
          - data/{SourceClassName}-{LocalId}.yaml :: data to transform
          - target/{SourceClassName}-{LocalId}.yaml :: expected output data
    """

    source_schema_directory_base: str = field(default_factory=lambda: "source")
    transform_specification_directory_base: str  = field(default_factory=lambda: "transform")
    source_data_directory_base: str  = field(default_factory=lambda: "data")
    target_data_directory_base: str  = field(default_factory=lambda: "target")

    input_formats: Optional[List[str]] = field(default_factory=lambda: ['yaml'])
    """Expected formats for input data"""

    output_formats: Optional[List[str]] = field(default_factory=lambda: ['yaml'])

    prefix_map: Optional[Mapping[str, str]] = None
    """Custom prefix map, for emitting RDF/turtle."""

    def process_directory(self, root_directory: Union[str, Path], **kwargs):
        """
        Process all transformations in a directory.

        :param root_directory:
        :return:
        """
        instructions = self.infer_instructions(root_directory)
        return self.process_instructions(instructions, root_directory, **kwargs)

    def infer_instructions(self, root_directory: Union[str, Path]) -> Instructions:
        """
        Infer instructions from either explicit yaml or directory layout.
        """
        if isinstance(root_directory, str):
            root_directory = Path(root_directory)
        if not root_directory.exists():
            raise ValueError(f"No such directory {root_directory}")
        instructions_file = root_directory / "instructions.yaml"
        if instructions_file.exists():
            with open(instructions_file) as file:
                return Instructions(**yaml.safe_load(file))
        source_schema_directory = root_directory / self.source_schema_directory_base
        if not source_schema_directory.exists():
            raise ValueError(f"Expected {source_schema_directory}")
        transform_specification_directory = root_directory / self.transform_specification_directory_base
        if not transform_specification_directory.exists():
            raise ValueError(f"Expected {transform_specification_directory}")
        input_schemas = glob.glob(os.path.join(str(source_schema_directory), "*.yaml"))
        if not input_schemas:
            raise ValueError(f"Expected schemas in {source_schema_directory}")
        instructions = Instructions(description="auto-inducted")
        for input_schema in input_schemas:
            transform_files = glob.glob(os.path.join(str(transform_specification_directory), "*.transform.yaml"))
            for transform_file in transform_files:
                tr = Transformation(source_schema=input_schema,
                                    transform_specification=transform_file)
                target_schema_base = None
                if len(input_schemas) != 1:
                    # resolve which schema the transform applies to
                    matches = re.match(r'^(\w+)-to-(\w+)\.', transform_file)
                    if not matches:
                        raise ValueError(f"Ambiguous: {transform_file}")
                    src, target_schema_base = matches.group(1, 2)
                    if src not in input_schema:
                        continue
                instructions.transformations.append(tr)
                data_files = glob.glob(os.path.join(str(self.source_data_directory_base), "*.yaml"))
                for data_file in data_files:
                    if target_schema_base and target_schema_base not in data_file:
                        continue
                    step = Step(source_data=data_file)
                    tr.steps.append(step)
                if not tr.steps:
                    raise ValueError(f"Could not infer steps from {data_files}")
        return instructions

    def process_instructions(self, instructions: Instructions, root_directory: Optional[Union[str, Path]], test_mode=False):
        """
        Process a set of instructions to transform one or more files.

        :param instructions:
        :param root_directory:
        :param test_mode:
        :return:
        """
        if isinstance(root_directory, str):
            directory = Path(root_directory)
        logging.info(f"Processing: {instructions.description}")
        for tr in instructions.transformations:
            source_schema_path = str(root_directory / tr.source_schema)
            sv = SchemaView(source_schema_path)
            transformer = ObjectTransformer()
            transformer.load_source_schema(source_schema_path)
            tr_path = str(root_directory / tr.transformation_specification)
            print(tr_path)
            transformer.load_transformer_specification(tr_path)
            for step in tr.steps:
                input_obj = yaml.safe_load(open(str(root_directory / step.source_data)))
                print(input_obj)
                target_obj = transformer.transform(input_obj)
                print(target_obj)

