import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from graphviz import Digraph
from linkml_runtime import SchemaView
from pydantic import BaseModel

from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import TransformationSpecification


class Record(BaseModel):
    """
    A simplified representation of a class, UML-style.
    """

    name: str
    source: str
    fields: List[Tuple[str, str]] = []

    @property
    def id(self):
        return f"{self.source}{self.name}"

    def __str__(self):
        return (
            f"""<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
            <TR><TD><B>{self.name}</B></TD></TR>
        """
            + "".join(
                [
                    f'<TR><TD SIDES="LRB" PORT="{f[0]}">{f[0]} : {f[1]}</TD></TR>'
                    for f in self.fields
                ]
            )
            + """
        </TABLE>>"""
        )


@dataclass
class GraphvizObject(CompiledSpecification):
    digraph: Digraph = None

    def render(self, file_path: str, format="png", view=False) -> None:
        """
        Renders a graphviz graph to a file.
        :param file_path:
        :return:
        """
        self.digraph.render(file_path, format=format, view=view)


class GraphvizCompiler(Compiler):
    """
    Compiles a Transformation Specification to GraphViz.
    """

    def compile(
        self, specification: TransformationSpecification, elements: Optional[List[str]] = None
    ) -> GraphvizObject:
        dg = Digraph(comment="UML Class Diagram", format="png")
        dg.attr(rankdir="LR")  # Set graph direction from left to right
        target_schemaview = self.derived_target_schemaview(specification)
        source_schemaview = self.source_schemaview

        records = []
        records += self.add_records(source_schemaview, "source")
        records += self.add_records(target_schemaview, "target")

        for record in records:
            dg.node(record.id, str(record), shape="plaintext")

        # Define the class nodes with fields in UML format using HTML-like labels
        # for precise control over the stacking of the fields
        for target_cn, cd in specification.class_derivations.items():
            source_cn = cd.populated_from
            if source_cn is None:
                source_cn = cd.name
            if elements is not None and target_cn not in elements:
                continue
            source_record = Record(name=source_cn, source="source")
            target_record = Record(name=target_cn, source="target")
            for sd in cd.slot_derivations.values():
                target_slot = sd.name
                target_id = f"{target_record.id}:{target_slot}"
                source_slot = sd.populated_from
                if source_slot:
                    source_id = f"{source_record.id}:{source_slot}"
                    dg.edge(source_id, target_id)
                elif sd.expr:
                    # TODO: do this in a less hacky way
                    tokens = re.findall(r"\w+", sd.expr)
                    for token in tokens:
                        if token not in source_schemaview.all_slots():
                            continue
                        dg.edge(f"{source_record.id}:{token}", target_id, style="dashed")
        return GraphvizObject(digraph=dg, serialization=dg.source)

    def add_records(self, schemaview: SchemaView, source: str) -> List[Record]:
        records = []
        for cn in schemaview.all_classes():
            record = Record(name=cn, source=source)
            for induced_slot in schemaview.class_induced_slots(cn):
                record.fields.append((induced_slot.name, induced_slot.range))
            records.append(record)
        return records
