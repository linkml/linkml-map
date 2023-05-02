from linkml_runtime import SchemaView

from linkml_transformer.datamodel.transformer_model import \
    TransformationSpecification


def induce_missing_values(
    specification: TransformationSpecification, source_schemaview: SchemaView
):
    """
    Infer missing values in a specification.

    Currently only uses copy directives.

    :param specification:
    :param source_schemaview:
    :return:
    """
    for cd in specification.class_derivations.values():
        if not cd.populated_from:
            cd.populated_from = cd.name
    for cd in specification.class_derivations.values():
        for sd in cd.slot_derivations.values():
            if sd.populated_from is None and sd.expr is None:
                sd.populated_from = sd.name
            if not sd.range:
                if sd.populated_from:
                    if cd.populated_from not in source_schemaview.all_classes():
                        continue
                    source_induced_slot = source_schemaview.induced_slot(
                        sd.populated_from, cd.populated_from
                    )
                    source_induced_slot_range = source_induced_slot.range
                    for range_cd in specification.class_derivations.values():
                        if range_cd.populated_from == source_induced_slot_range:
                            sd.range = range_cd.name
