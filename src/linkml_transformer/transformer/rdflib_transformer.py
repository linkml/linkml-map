from dataclasses import dataclass

from linkml_transformer.transformer.transformer import Transformer


@dataclass
class RdflibTransformer(Transformer):
    """
    A transformer that works on in-memory rdflib Graphs.

    NOT IMPLEMENTED
    """
