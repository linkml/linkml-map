import logging
from dataclasses import dataclass
from typing import Type, Any, Union, List, Iterator

from linkml.utils.datautils import infer_root_class
from linkml_runtime.linkml_model import SlotDefinition, EnumDefinition, ClassDefinitionName
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.eval_utils import eval_expr
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_runtime.utils.inference_utils import infer_slot_value, obj_as_dict_nonrecursive
from linkml_transformer.datamodel.transformer_model import TransformationSpecification
from linkml_transformer.transformer.transformer import Transformer
from linkml_runtime.index.object_index import ObjectIndex


logger = logging.getLogger(__name__)

@dataclass
class ObjectTransformer(Transformer):
    """
    A Transformer that works on in-memory objects.

    This works by recursively
    """
    object_index: ObjectIndex = None

    def index(self, source_obj: YAMLRoot):
        """
        Create an index over a container object.

        :param source_obj:
        :return:
        """
        self.object_index = ObjectIndex(source_obj, schemaview=self.source_schemaview)

    def _transform_any(self, obj: Any, target_class: Type[YAMLRoot], parent_slot: SlotDefinition) -> YAMLRoot:
        logger.debug(f"T={type(obj)} // {obj}")
        if isinstance(obj, EnumDefinitionImpl):
            return str(obj)
        else:
            return obj

    def transform(self, source_obj: YAMLRoot, target_class: Type[YAMLRoot] = None) -> YAMLRoot:
        """
        Transform a source object into a target object.
        :param source_obj:
        :param target_class:
        :return:
        """
        tgt_mod = self.target_module
        spec = self.specification
        typ = type(source_obj)
        try:
            cls_name = typ.class_name
        except AttributeError:
            # primitive
            if isinstance(source_obj, EnumDefinitionImpl):
                return str(source_obj)
            return source_obj
        logger.debug(f"\nSource object type={cls_name}")
        # use populated-from to pick the class derivation
        matching_tgt_class_derivs = [deriv for deriv in spec.class_derivations.values() if deriv.populated_from == cls_name]
        logger.debug(f"Target class derivs={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            raise ValueError(f"Could not find what to derive from a source {cls_name}")
        [class_deriv] = matching_tgt_class_derivs
        tgt_class_name = class_deriv.name
        tgt_class = getattr(tgt_mod, tgt_class_name)
        tgt_attrs = {}
        for slot_derivation in class_deriv.slot_derivations.values():
            v = None
            if slot_derivation.populated_from:
                v = getattr(source_obj, slot_derivation.populated_from, None)
                logger.debug(f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {source_obj}")
            elif slot_derivation.expr:
                if self.object_index:
                    ctxt_obj = self.object_index.bless(source_obj)
                    ctxt_dict = {k: getattr(ctxt_obj, k) for k in ctxt_obj._attributes()}
                else:
                    ctxt_dict = obj_as_dict_nonrecursive(source_obj)
                v = eval_expr(slot_derivation.expr, **ctxt_dict)
            else:
                v = getattr(source_obj, slot_derivation.name)
            if v is not None:
                if isinstance(v, list):
                    v = [self.transform(v1) for v1 in v]
                else:
                    v = self.transform(v)
                    #v = self._transform_any(v, None, None)
                tgt_attrs[slot_derivation.name] = v
        logger.debug(tgt_class)
        logger.debug(tgt_attrs)
        return tgt_class(**tgt_attrs)

    def derive(
            self,
            source_root_object: YAMLRoot,
            target_class: Union[ClassDefinitionName, Type[YAMLRoot]] = None,
            source_object: YAMLRoot = None
    ) -> YAMLRoot:
        """
        Derives an instance of target_class

        :param target_class:
        :param source_object:
        :return:
        """
        spec = self.specification
        if target_class is None:
            target_class = infer_root_class(self.target_schemaview)
        if target_class is None:
            raise ValueError(f"Cannot infer tree root")
        target_class_name = self.ensure_class_name(target_class)
        target_class_type = self.ensure_type(target_class)
        if target_class_name not in spec.class_derivations:
            yield ValueError(f"{target_class_name} has no derivation rules")
        class_derivation = spec.class_derivations[target_class_name]
        target_attrs = {}
        for sd in class_derivation.slot_derivations.values():
            v = None
            if sd.populated_from:
                v = getattr(source_object, sd.populated_from, None)
            elif sd.expr:
                eval_expr(sd.expr,  **obj_as_dict_nonrecursive(source_object))
            else:
                v = getattr(obj, sd.name)
            if v is not None:
                v = self.transform(v)
                #v = self._transform_any(v, None, None)
                target_attrs[sd.name] = v
        return target_class_type(**target_attrs)

    def derive_multi(
            self,
            source_root_object: YAMLRoot,
            target_class: Union[ClassDefinitionName, Type[YAMLRoot]] = None,
            source_object: YAMLRoot = None
    ) -> Iterator[YAMLRoot]:
        """
        Derives all instances of TargetClass

        :param target_class:
        :param source_object:
        :return:
        """
        spec = self.specification
        if target_class is None:
            target_class = infer_root_class(self.target_schemaview)
        if target_class is None:
            raise ValueError(f"Cannot infer tree root")
        target_class_name = self.ensure_class_name(target_class)
        target_class_type = self.ensure_type(target_class)
        if target_class_name not in spec.class_derivations:
            yield ValueError(f"{target_class_name} has no derivation rules")
        class_derivation = spec.class_derivations[target_class_name]
        target_attrs = {}
        if class_derivation.joins:
            raise NotImplementedError
        for sd in class_derivation.slot_derivations.values():
            v = None
            if sd.populated_from:
                v = getattr(source_object, sd.populated_from, None)
            elif sd.expr:
                eval_expr(sd.expr,  **obj_as_dict_nonrecursive(source_object))
            else:
                v = getattr(obj, sd.name)
            if v is not None:
                v = self._transform_any(v, None, None)
                target_attrs[sd.name] = v
        return target_class_type(**target_attrs)


    def ensure_class_name(self, cls:  Union[str, ClassDefinitionName, Type[YAMLRoot]]) -> str:
        """
        For an object that is either a class name or a python type, ensure return value is the class name

        :param cls:
        :return:
        """
        if isinstance(cls, str):
            return cls
        else:
            return cls.class_name

    def ensure_type(self, cls:  Union[str, ClassDefinitionName, Type[YAMLRoot]]) -> Type[YAMLRoot]:
        """
        For an object that is either a class name or a python type, ensure return value is the type

        :param cls:
        :return:
        """
        if isinstance(cls, str):
            return getattr(self.target_module, cls)
        else:
            return cls


