import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

from linkml_runtime.index.object_index import ObjectIndex
from linkml_runtime.utils.eval_utils import eval_expr
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_transformer.transformer.transformer import OBJECT_TYPE, Transformer
from linkml_transformer.utils.dynamic_object import DynObj, dynamic_object

DICT_OBJ = Dict[str, Any]


logger = logging.getLogger(__name__)


@dataclass
class ObjectTransformer(Transformer):
    """
    A Transformer that works on in-memory dict objects.

    This works by recursively
    """

    object_index: ObjectIndex = None

    def index(self, source_obj: Any, target: str = None):
        """
        Create an index over a container object.

        :param source_obj:
        :return:
        """
        if isinstance(source_obj, dict):
            if target is None:
                [target] = [
                    c.name
                    for c in self.source_schemaview.all_classes().values()
                    if c.tree_root
                ]
            if target is None:
                raise ValueError(
                    f"target must be passed if source_obj is dict: {source_obj}"
                )
            source_obj_typed = dynamic_object(
                source_obj, self.source_schemaview, target
            )
            self.object_index = ObjectIndex(
                source_obj_typed, schemaview=self.source_schemaview
            )
        else:
            self.object_index = ObjectIndex(
                source_obj, schemaview=self.source_schemaview
            )

    def transform(
        self,
        source_obj: OBJECT_TYPE,
        source_type: str = None,
    ) -> DICT_OBJ:
        """
        Transform a source object into a target object.

        :param source_obj:
        :param source_type:
        :return:
        """
        sv = self.source_schemaview
        if source_type is None:
            [source_type] = [c.name for c in sv.all_classes().values() if c.tree_root]
        if source_type in sv.all_types():
            # TODO: type derivations
            return source_obj
        if source_type in sv.all_enums():
            # TODO: enum derivations
            return str(source_obj)
        if isinstance(source_obj, (BaseModel, YAMLRoot)):
            source_obj_typed = source_obj
            source_obj = vars(source_obj)
        else:
            source_obj_typed = None
        if not isinstance(source_obj, dict):
            logger.warning(f"Unexpected: {source_obj} for type {source_type}")
            return source_obj
        source_type_class = sv.get_class(source_type)
        class_deriv = self._get_class_derivation(source_type)
        tgt_attrs = {}
        for slot_derivation in class_deriv.slot_derivations.values():
            v = None
            source_class_slot = None
            target_class_slot = None
            if slot_derivation.populated_from:
                v = source_obj.get(slot_derivation.populated_from, None)
                source_class_slot = sv.induced_slot(
                    slot_derivation.populated_from, source_type
                )
                logger.debug(
                    f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {source_obj}"
                )
            elif slot_derivation.expr:
                if self.object_index:
                    if not source_obj_typed:
                        source_obj_dyn = dynamic_object(source_obj, sv, source_type)
                    else:
                        source_obj_dyn = source_obj_typed
                    ctxt_obj = self.object_index.bless(source_obj_dyn)
                    ctxt_dict = {
                        k: getattr(ctxt_obj, k)
                        for k in ctxt_obj._attributes()
                        if not k.startswith("_")
                    }
                else:
                    # ctxt_dict = source_obj
                    do = dynamic_object(source_obj, sv, source_type)
                    ctxt_dict = vars(do)
                v = eval_expr(slot_derivation.expr, **ctxt_dict, NULL=None)
            else:
                source_class_slot = sv.induced_slot(slot_derivation.name, source_type)
                v = source_obj.get(slot_derivation.name, None)
            if source_class_slot and v is not None:
                source_class_slot_range = source_class_slot.range
                if source_class_slot.multivalued:
                    if isinstance(v, list):
                        v = [self.transform(v1, source_class_slot_range) for v1 in v]
                    elif isinstance(v, dict):
                        v = [self.transform(v1, source_class_slot_range) for v1 in v]
                    else:
                        v = [v]
                else:
                    v = self.transform(v, source_class_slot_range)
            tgt_attrs[str(slot_derivation.name)] = v
        return tgt_attrs

    def transform_object(
        self,
        source_obj: Union[YAMLRoot, BaseModel],
        target_class: Optional[Union[Type[YAMLRoot], Type[BaseModel]]] = None,
    ) -> Union[YAMLRoot, BaseModel]:
        typ = type(source_obj)
        typ_name = typ.__name__
        # if isinstance(source_obj, YAMLRoot):
        #    source_obj_dict = json_dumper.to_dict(source_obj)
        # elif isinstance(source_obj, BaseModel):
        #    source_obj_dict = source_obj.dict()
        # else:
        #    raise ValueError(f"Do not know how to handle type: {typ}")
        tr_obj_dict = self.transform(source_obj, typ_name)
        return target_class(**tr_obj_dict)
