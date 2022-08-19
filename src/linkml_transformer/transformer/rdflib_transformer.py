from dataclasses import dataclass
from typing import Type

import rdflib
from linkml_runtime.dumpers import rdflib_dumper
from linkml_runtime.loaders import rdflib_loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_transformer.transformer.transformer import Transformer


@dataclass
class RdflibTransformer(Transformer):

    def transform(self, obj: YAMLRoot, target_class: Type[YAMLRoot]) -> YAMLRoot:
        g = rdflib_dumper.as_rdf_graph(obj, self.source_schemaview)
        target_g = self.transform_graph(g)
        return rdflib_loader.load(target_g, schemaview=self.target_schemaview, target_class=target_class)

    def transform_graph(self, g: rdflib.Graph):
        g2 = rdflib.Graph()
        for t in g.triples((None, None, None)):
            g2.add(t)
        return g2



