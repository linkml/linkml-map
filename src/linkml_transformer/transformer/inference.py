import re

from linkml_runtime import SchemaView

from linkml_transformer.datamodel.transformer_model import (
    SlotDerivation, TransformationSpecification)


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
        src_cls_name = cd.populated_from
        src_cls = source_schemaview.get_class(src_cls_name)
        for slot_match, directive in cd.copy_directives.items():
            for sn in source_schemaview.class_slots(src_cls.name):
                if sn in cd.slot_derivations:
                    continue
                # if slot_match == "*" or re.match(slot_match, sn):
                #    sd = SlotDerivation(name=sn, populated_from=sn)
                #    print(f"Adding {src_cls_name} . {sd}")
                #    cd.slot_derivations[sd.name] = sd
