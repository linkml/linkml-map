"""
meta-circular interpreter for evaluating python expressions.

 - See `<https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string>`_

TODO: move to core
"""

import ast
import operator as op
from collections.abc import Mapping

# supported operators
from typing import Any

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
}
compare_operators = {ast.Eq: op.eq, ast.Lt: op.lt, ast.LtE: op.le, ast.Gt: op.gt, ast.GtE: op.ge}


def eval_conditional(*conds: list[tuple[bool, Any]]) -> Any:
    """
    Evaluate a conditional.

    >>> x = 10
    >>> eval_conditional((x < 25, 'low'), (x > 25, 'high'), (True, 'low'))
    'low'

    :param conds: conditionals to be evaluated
    :return: Any
    """
    for is_true, val in conds:
        if is_true:
            return val
    return None


funcs = {
    "max": (True, max),
    "min": (True, min),
    "len": (True, len),
    "str": (False, str),
    "strlen": (False, len),
    "case": (False, eval_conditional),
}


class UnsetValueError(Exception):
    pass


def eval_expr_with_mapping(expr: str, mapping: Mapping) -> Any:
    """
    Evaluate a given expression, with restricted syntax.

    This function is equivalent to eval_expr where **kwargs has been switched to a Mapping (eg. a dictionary).
    See eval_expr for details.
    """
    if expr == "None":
        # TODO: do this as part of parsing
        return None
    try:
        return eval_(ast.parse(expr, mode="eval").body, mapping)
    except UnsetValueError:
        return None


def eval_expr(expr: str, **kwargs) -> Any:
    """
    Evaluate a given expression, with restricted syntax.

    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0

    Variables:

    variables can be passed

    >>> eval_expr('{x} + {y}', x=1, y=2)
    3

    Nulls:

    - If a variable is enclosed in {}s then entire expression will eval to None if variable is unset

    >>> print(eval_expr('{x} + {y}', x=None, y=2))
    None


    Functions:

    - only a small set of functions are currently supported. All SPARQL functions will be supported in future

    >>> eval_expr('strlen("a" + "bc")')
    3

    Paths:

    - Expressions such as `person.name` can be used on objects to lookup by attribute/slot
    - Paths can be chained, e.g. `person.address.street`
    - Operations on lists are distributed, e.g `container.persons.name` will return a list of names
    - Similarly `strlen(container.persons.name)` will return a list whose members are the lengths of all names

    :param expr: expression to evaluate
    """
    return eval_expr_with_mapping(expr, kwargs)


def eval_(node, bindings=None):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Str):
        if "s" in vars(node):
            return node.s
        return node.value
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.NameConstant):
        # can be removed when python 3.7 is no longer supported
        return node.value
    if isinstance(node, ast.Name):
        if not bindings:
            bindings = {}
        return bindings.get(node.id)
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Index):
            # required for python 3.7
            k = eval_(node.slice.value, bindings)
        else:
            k = eval_(node.slice, bindings)
        v = eval_(node.value, bindings)
        return v[k]
    if isinstance(node, ast.Attribute):
        # e.g. for person.name, this returns the val of person
        v = eval_(node.value, bindings)

        # lookup attribute, potentially distributing the results over collections
        def _get(obj: Any, k: str, recurse=True) -> Any:
            if isinstance(obj, dict):
                # dicts are treated as collections; distribute results
                if recurse:
                    return [_get(e, k, False) for e in obj.values()]
                return obj.get(k)
            if isinstance(obj, list):
                # attributes are distributed over lists
                return [_get(e, k, False) for e in obj]
            if obj is None:
                return None
            return getattr(obj, k)

        return _get(v, node.attr)
    if isinstance(node, ast.List):
        return [eval_(x, bindings) for x in node.elts]
    if isinstance(node, ast.Set):
        # sets are not part of the language; we use {x} as notation for x
        if len(node.elts) != 1:
            msg = "The {} must enclose a single variable"
            raise ValueError(msg)
        e = node.elts[0]
        if not isinstance(e, ast.Name):
            msg = "The {} must enclose a variable"
            raise ValueError(msg)
        v = eval_(e, bindings)
        if v is None:
            msg = f"{e} is not set"
            raise UnsetValueError(msg)
        return v
    if isinstance(node, ast.Tuple):
        return tuple([eval_(x, bindings) for x in node.elts])
    if isinstance(node, ast.Dict):
        return {
            eval_(k, bindings): eval_(v, bindings)
            for k, v in zip(node.keys, node.values, strict=False)
        }
    if isinstance(node, ast.Compare):  # <left> <operator> <right>
        if len(node.ops) != 1:
            msg = f"Must be exactly one op in {node}"
            raise ValueError(msg)
        if type(node.ops[0]) not in compare_operators:
            msg = f"Not implemented: {node.ops[0]} in {node}"
            raise NotImplementedError(msg)
        py_op = compare_operators[type(node.ops[0])]
        if len(node.comparators) != 1:
            msg = f"Must be exactly one comparator in {node}"
            raise ValueError(msg)
        right = node.comparators[0]
        return py_op(eval_(node.left, bindings), eval_(right, bindings))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left, bindings), eval_(node.right, bindings))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand, bindings))
    # elif isinstance(node, ast.Match):
    #    # implementing this would restrict python version to 3.10
    #    # https://stackoverflow.com/questions/60208/replacements-for-switch-statement-in-python
    #    raise NotImplementedError(f'Not supported')
    if isinstance(node, ast.IfExp):
        if eval_(node.test, bindings):
            return eval_(node.body, bindings)
        return eval_(node.orelse, bindings)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            fn = node.func.id
            if fn in funcs:
                takes_list, func = funcs[fn]
                args = [eval_(x, bindings) for x in node.args]
                if isinstance(args[0], list) and not takes_list:
                    return [func(*[x] + args[1:]) for x in args[0]]
                return func(*args)
        msg = f"Call {node.func} not implemented. node = {node}"
        raise NotImplementedError(msg)
    raise TypeError(node)
