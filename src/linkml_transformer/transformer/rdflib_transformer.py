from dataclasses import dataclass
from typing import Type

import rdflib
from linkml_runtime.dumpers import rdflib_dumper
from linkml_runtime.loaders import rdflib_loader
from linkml_runtime.utils.yamlutils import YAMLRoot

from linkml_transformer.transformer.transformer import Transformer


@dataclass
class RdflibTransformer(Transformer):
    """
    A transformer that works on in-memory rdflib Graphs.

    NOT IMPLEMENTED
    """
