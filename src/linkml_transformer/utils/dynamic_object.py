from typing import Any

from linkml_runtime import SchemaView


class DynObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self) -> str:
        return str(vars(self))

    def __getattr__(self, p: str) -> Any:
        return vars(self).get(p, None)


def dynamic_object(obj: dict, sv: SchemaView, target: str):
    """
    Generate a dynamic object from a dict.

    :param obj:
    :param sv:
    :param target:
    :return:
    """
    if target in sv.all_enums():
        return obj
    if target in sv.all_types():
        return obj
    if not isinstance(obj, dict):
        return obj
    attrs = {}
    for k, v in obj.items():
        slot = sv.induced_slot(k, target)
        rng = slot.range
        if slot.multivalued:
            if isinstance(v, list):
                v = [dynamic_object(x, sv, rng) for x in v]
            if isinstance(v, dict):
                v = {xk: dynamic_object(x, sv, rng) for xk, x in v.items()}
                id_slot = sv.get_identifier_slot(slot.range)
                for k1, v1 in v.items():
                    setattr(v1, id_slot.name, k1)
        else:
            v = dynamic_object(v, sv, rng)
        attrs[k] = v
    cls = type(target, (DynObj,), {})
    return cls(**attrs)
