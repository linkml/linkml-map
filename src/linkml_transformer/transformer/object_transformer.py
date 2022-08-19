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


@dataclass
class ObjectTransformer(Transformer):
    """
    A Transformer that works on in-memory objects
    """

    def _transform_any(self, obj: Any, target_class: Type[YAMLRoot], parent_slot: SlotDefinition) -> YAMLRoot:
        print(f"T={type(obj)} // {obj}")
        if isinstance(obj, EnumDefinitionImpl):
            return str(obj)
        else:
            return obj

    def transform(self, obj: YAMLRoot, target_class: Type[YAMLRoot]) -> YAMLRoot:
        tgt_mod = self.target_module
        spec = self.specification
        typ = type(obj)
        cls_name = typ.class_name
        print(cls_name)
        [class_deriv] = [deriv for deriv in spec.class_derivations.values() if deriv.populated_from == cls_name]
        print(class_deriv)
        tgt_class_name = class_deriv.name
        tgt_class = getattr(tgt_mod, tgt_class_name)
        attrs = {}
        for sd in class_deriv.slot_derivations.values():
            v = None
            if sd.populated_from:
                v = getattr(obj, sd.populated_from, None)
            elif sd.expr:
                eval_expr(sd.expr,  **obj_as_dict_nonrecursive(obj))
            else:
                v = getattr(obj, sd.name)
            if v is not None:
                v = self._transform_any(v, None, None)
                attrs[sd.name] = v
        print(tgt_class)
        print(attrs)
        return tgt_class(**attrs)

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
                v = self._transform_any(v, None, None)
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


