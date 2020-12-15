from typing import Type, Literal, Any, List
import argparse
import inspect


def _is_literal(t: Type) -> bool:
    if '__origin__' not in t.__dict__:
        return False
    origin = t.__dict__['__origin__']
    return origin is Literal


def _get_literal_type(t: Type) -> Type:
    assert _is_literal(t)
    args = t.__dict__['__args__']
    types = set([type(arg) for arg in args])
    if len(types) == 0:
        raise Exception(f'Malformed literal: {t}, found 0 choices.')
    elif len(types) > 1:
        return Any
    else:
        return types.pop()


def _get_literal_type_choices(t: Type) -> List[Any]:
    assert _is_literal(t)
    return list(t.__dict__['__args__'])


def build_parser_for_experiment(
        run_experiment_function,
        required_args=(('run_idx', str), ('data_path', str))
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    assert inspect.isfunction(run_experiment_function)
    sig = inspect.signature(run_experiment_function)
    acceptable_types = [int, str, float, bool]
    unsatisfied_reqs = dict(required_args)
    for param_name in sig.parameters.keys():
        param_type: Type = sig.parameters[param_name].annotation
        if param_name in unsatisfied_reqs.keys():
            if param_type not in acceptable_types:
                raise Exception(f'Required arg "{param_name}" must have annotation <{param_type}>.')
            del unsatisfied_reqs[param_name]
        if _is_literal(param_type):
            assert (inner_type := _get_literal_type(param_type)) in acceptable_types
            parser.add_argument(
                f'--{param_name}', type=inner_type, choices=_get_literal_type_choices(param_type), required=True)
        else:
            if param_type == bool:
                parser.add_argument(f'--{param_name}', action='store_true')
            else:
                parser.add_argument(f'--{param_name}', type=param_type, required=True)
    if unsatisfied_reqs:
        raise Exception(f'Function needs arguments: {set(unsatisfied_reqs.keys())}.')
    return parser