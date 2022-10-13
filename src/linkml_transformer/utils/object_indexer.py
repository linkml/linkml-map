"""TODO: this will be replaced with newer versions of linkml-runtime

See: https://github.com/linkml/linkml-runtime/pull/211
"""
import logging
from typing import Mapping, Any, Optional, Tuple, List

from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot


class ObjectIndex:
    """
    Index of proxy objects.
    """
    def __init__(self, obj: YAMLRoot, schemaview: SchemaView):
        self._obj = obj
        self._schemaview = schemaview
        self._class_map = schemaview.class_name_mappings()
        self._source_object_cache: Mapping[str, Any] = {}
        self._proxy_object_cache: Mapping[str, "ProxyObject"] = {}
        self._index(obj)

    def _index(self, obj: Any):
        if obj is None:
            return None
        if isinstance(obj, list):
            return [self._index(v) for v in obj]
        if isinstance(obj, dict):
            return {k: self._index(v) for k, v in obj.items()}
        cls_name = type(obj).__name__
        if cls_name in self._class_map:
            cls = self._class_map[cls_name]
            id_slot = self._schemaview.get_identifier_slot(cls.name)
            if id_slot:
                id_val = getattr(obj, id_slot.name)
                self._source_object_cache[(cls.name, id_val)] = obj
            for v in vars(obj).values():
                self._index(v)
        else:
            return obj

    def bless(self, obj: Any) -> "ProxyObject":
        """
        Generate a proxy object for a given domain object.

        The proxy object will mimic the domain object

        :param obj:
        :return:
        """
        k = self._key(obj)
        if k:
            if k not in self._proxy_object_cache:
                obj2 = ProxyObject(obj, _db=self)
                self._proxy_object_cache[k] = obj2
                return obj2
            else:
                return self._proxy_object_cache[k]
        else:
            return ProxyObject(obj, _db=self)

    def _key(self, obj: Any) -> Optional[Tuple[str, YAMLRoot]]:
        cls_name = type(obj).__name__
        cls = self._class_map[cls_name]
        id_slot = self._schemaview.get_identifier_slot(cls.name)
        if id_slot:
            id_val = getattr(obj, id_slot.name)
            return cls.name, id_val

    @property
    def proxy_object_cache_size(self) -> int:
        return len(self._proxy_object_cache.keys())

    @property
    def source_object_cache_size(self) -> int:
        return len(self._source_object_cache.keys())

    def clear_proxy_object_cache(self):
        self._proxy_object_cache = {}


class ProxyObject:
    """
    An object that mirrors a domain object.

    This will automatically expand foreign key references.
    """

    def __init__(self, obj: Any, _db: ObjectIndex, **kwargs):
        self._db = _db
        self._shadowed = obj

    def __str__(self) -> str:
        return f"ProxyFor: {str(self._shadowed)}"

    def __getattr__(self, p: str) -> Any:
        obj = self._shadowed
        cls = self._db._class_map[type(obj).__name__]
        slot = self._db._schemaview.induced_slot(p, cls.name)
        v = getattr(obj, p)
        return self._map(v, slot.range)

    def __getattribute__(self, attribute):
        if attribute == '__dict__':
            return {k: getattr(self, k, None) for k in vars(self._shadowed).keys()}
        else:
            return object.__getattribute__(self, attribute)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            setattr(self._shadowed, key, value)

    def _map(self, obj: Any, in_range: str) -> Any:
        if isinstance(obj, list):
            r = [self._map(v, in_range) for v in obj]
            return r
        if isinstance(obj, dict):
            return {k: self._map(v, in_range) for k, v in obj.items()}
        cls_name = type(obj).__name__
        if cls_name in self._db._class_map:
            return self._db.bless(obj)
        if in_range in self._db._class_map:
            # FK reference
            k = (in_range, obj)
            cache = self._db._source_object_cache
            if k in cache:
                source_obj = cache[k]
                return self._db.bless(source_obj)
            else:
                logging.error(f"Making stub for {k}")
                return obj
        return obj

    def _attributes(self) -> List[str]:
        return vars(self._shadowed).keys()

