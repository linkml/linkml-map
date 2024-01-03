from typing import Optional, List, Tuple

from graphviz import Digraph
from pydantic import BaseModel

from project.transformer_model import TransformationSpecification


class Record(BaseModel):
    """
    A record is a collection of fields.
    """
    name: str
    fields: List[Tuple[str, str]] = []

    def __str__(self):
        return f'<{self.name}> {self.name}|' + '|'.join([f'<{f[0]}> {f[0]} : {f[1]}' for f in self.fields])


def generate_graphviz_graph(specification: TransformationSpecification, elements: Optional[List[str]] = None) -> Digraph:
    """
    Generates a graphviz graph from a transformer specification.

    :param specification:
    :param elements:
    :return:
    """
    dg = Digraph(comment='UML Class Diagram', format='png')
    dg.attr(rankdir='LR')  # Set graph direction from left to right

    # Define the class nodes with fields in UML format using HTML-like labels
    # for precise control over the stacking of the fields
    for target_cn, cd in specification.class_derivations.items():
        source_cn = cd.populated_from
        if source_cn is None:
            source_cn = cd.name
        if elements is not None and target not in elements:
            continue
        source_record = Record(name=source_cn)
        target_record = Record(name=target_cn)
        for slot_name, sd in cd.slot_derivations.items():
            source_slot = sd.populated_from
            target_slot = sd.name
            source_id = f'{source_cn}:{source_slot}'
            target_id = f'{target_cn}:{target_slot}'
            dg.edge(source_id, target_id)
            source_record.fields.append((source_slot, 'string'))
            target_record.fields.append((target_slot, 'string'))
        dg.node(target_cn, str(source_record), shape='record')
        dg.node(source_cn, str(target_record), shape='record')
    return dg


def render(dot: Digraph, file_path: str) -> None:
    """
    Renders a graphviz graph to a file.
    :param dot:
    :param file_path:
    :return:
    """
    dot.render(file_path, format='png', view=False)
