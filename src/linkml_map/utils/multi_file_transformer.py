"""Iterate through all examples in a folder testing them for validity.

"""

import glob
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Optional, Union

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from pydantic import BaseModel

from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer


class Step(BaseModel):
    source_data: str
    target_data: Optional[str] = None
    source_class: str = None
    target_class: str = None


class Transformation(BaseModel):
    description: Optional[str] = None
    source_schema: str = None
    target_schema: str = None
    transformation_specification: str = None
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
    transform_specification_directory_base: str = field(default_factory=lambda: "transform")
    source_data_directory_base: str = field(default_factory=lambda: "data")
    target_schema_directory_base: str = field(default_factory=lambda: "target")
    target_data_directory_base: str = field(default_factory=lambda: "output")

    input_formats: Optional[List[str]] = field(default_factory=lambda: ["yaml"])
    """Expected formats for input data"""

    output_formats: Optional[List[str]] = field(default_factory=lambda: ["yaml"])

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
        transform_specification_directory = (
            root_directory / self.transform_specification_directory_base
        )
        if not transform_specification_directory.exists():
            raise ValueError(f"Expected {transform_specification_directory}")
        target_schema_directory = root_directory / self.target_schema_directory_base
        input_schemas = glob.glob(os.path.join(str(source_schema_directory), "*.yaml"))
        if not input_schemas:
            raise ValueError(f"Expected schemas in {source_schema_directory}")
        transform_files = glob.glob(
            os.path.join(str(transform_specification_directory), "*.transform.yaml")
        )
        instructions = Instructions(description="auto-inducted")
        for input_schema in input_schemas:
            for transform_file in transform_files:
                tr = Transformation(
                    source_schema=input_schema,
                    transformation_specification=transform_file,
                    steps=[],
                )
                target_schema_base = None
                if len(input_schemas) != 1:
                    # resolve which schema the transform applies to
                    matches = re.match(r"^(\w+)-to-(\w+)\.", transform_file)
                    if not matches:
                        raise ValueError(f"Ambiguous: {transform_file}")
                    src, target_schema_base = matches.group(1, 2)
                    if src not in input_schema:
                        continue
                instructions.transformations.append(tr)
                data_files = glob.glob(
                    os.path.join(str(root_directory / self.source_data_directory_base), "*.yaml")
                )
                for data_file in data_files:
                    if target_schema_base and target_schema_base not in data_file:
                        continue
                    target_data = str(Path(self.target_data_directory_base) / Path(data_file).name)
                    target_data = target_data.replace(".yaml", ".transformed.yaml")
                    step = Step(source_data=data_file, target_data=target_data)
                    step.source_class = Path(data_file).stem.split("-")[-2]
                    tr.steps.append(step)
                target_schemas = glob.glob(os.path.join(str(target_schema_directory), "*.yaml"))
                if len(target_schemas) > 1:
                    target_schemas = [s for s in target_schemas if target_schema_base in s]
                    if len(target_schemas) != 1:
                        raise ValueError(
                            f"Could not determine target schema from: {target_schemas}"
                        )
                if target_schemas:
                    tr.target_schema = target_schemas[0]
                else:
                    tr.target_schema = str(Path(target_schema_directory) / "target.yaml")
                if not tr.steps:
                    raise ValueError(f"Could not infer steps from {data_files}")
                if not tr.transformation_specification:
                    raise ValueError(f"No spec {tr}")
        return instructions

    def process_instructions(
        self,
        instructions: Instructions,
        root_directory: Optional[Union[str, Path]],
        output_directory=None,
        test_mode=False,
    ):
        """
        Process a set of instructions to transform one or more files.

        :param instructions:
        :param root_directory:
        :param output_directory:
        :param test_mode:
        :return:
        """
        if isinstance(root_directory, str):
            root_directory = Path(root_directory)
        if isinstance(output_directory, str):
            root_directory = Path(output_directory)
        if not output_directory:
            output_directory = root_directory
        logging.info(f"Processing: {instructions.description}")
        for tr in instructions.transformations:
            source_schema_path = str(root_directory / tr.source_schema)
            sv = SchemaView(source_schema_path)
            transformer = ObjectTransformer(unrestricted_eval=True)
            transformer.load_source_schema(source_schema_path)
            tr_path = str(root_directory / tr.transformation_specification)
            transformer.load_transformer_specification(tr_path)
            if tr.target_schema:
                target_schema_path = root_directory / tr.target_schema
                mapper = SchemaMapper()
                mapper.source_schemaview = sv
                target_schema_obj = mapper.derive_schema(transformer.specification)
                if not target_schema_path.exists():
                    target_schema_path.parent.mkdir(exist_ok=True, parents=True)
                    yaml_dumper.dump(target_schema_obj, str(target_schema_path))
            for step in tr.steps:
                input_obj = yaml.safe_load(open(str(root_directory / step.source_data)))
                transformer.index(input_obj, step.source_class)
                target_obj = transformer.map_object(input_obj, source_type=step.source_class)
                if step.target_data:
                    out_path = output_directory / step.target_data
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    if out_path.exists():
                        line1 = open(str(out_path)).readline()
                        overwrite = "OVERWRITE" in line1
                        with open(str(out_path)) as f:
                            compare_obj = yaml.safe_load(f)
                            if compare_obj != target_obj:
                                if test_mode and not overwrite:
                                    raise ValueError(
                                        f"Output different than expected: {compare_obj}"
                                    )
                                else:
                                    logging.warning(f"Different: {compare_obj}")
                    with open(str(out_path), "w", encoding="utf-8") as f:
                        yaml_str = yaml.dump(target_obj, sort_keys=False)
                        f.write(yaml_str)
