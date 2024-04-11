from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader

from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.compiler.templates import TEMPLATE_DIR
from linkml_map.datamodel.transformer_model import TransformationSpecification


@dataclass
class J2BasedCompiler(Compiler):
    """
    Compiles a Transformation Specification using a Jinja2 template.
    """

    template_dir: str = None
    """The directory containing the Jinja2 template."""

    template_name: str = None
    """The name of the Jinja2 template."""

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        template_dir = self.template_dir
        if not template_dir:
            template_dir = TEMPLATE_DIR
        if not template_dir:
            raise ValueError("template_dir must be set")
        loader = FileSystemLoader(template_dir)
        env = Environment(loader=loader, autoescape=True)
        if not self.template_name:
            raise ValueError("template_name must be set")
        template = env.get_template(self.template_name)
        rendered = template.render(
            spec=specification,
        )
        return CompiledSpecification(serialization=rendered)
