import itertools
from typing import List, Callable, Dict, Optional, Iterable, Union, TypeVar
from experiment_suite.scheduler.utils import Run
import time
import os
import pickle
import sys

T = TypeVar('T')
Primitive = Union[int, str, bool, float]
Kwargs = Dict[str, Primitive]
KwargFilter = Callable[[Kwargs], bool]
Experiment = Callable[[str, Kwargs], None]

class Sweep:

    def __init__(self):
        self._sweep_args: Dict[str, List[Primitive]] = dict()
        self._filters: List[KwargFilter] = []
        self._enum_funcs: Dict[str, Callable[[int], Primitive]] = dict()
        self._used_names = set()

    def copy(self) -> 'Sweep':
        new_sweep = Sweep()
        for name, vals in self._sweep_args.items():
            new_sweep.add_product(name, vals)
        for name, vals in self._enum_funcs.items():
            new_sweep.add_enumeration(name, vals)
        for f in self._filters:
            new_sweep.add_filter(f)
        return new_sweep

    def add_product(
            self,
            name: str,
            values: List[Primitive]
    ) -> None:
        if name in self._used_names:
            raise Exception(f'Name {name} already in use.')
        self._used_names.add(name)
        self._sweep_args[name] = list(values[:])

    def add_enumeration(
            self,
            name: str,
            enum_func: Callable[[int], Primitive]
    ) -> None:
        if name in self._used_names:
            raise Exception(f'Name {name} already in use.')
        self._enum_funcs[name] = enum_func

    def add_filter(
            self,
            filter_func: KwargFilter
    ) -> None:
        self._filters.append(filter_func)

    def __iter__(self) -> Iterable[Kwargs]:
        sorted_items = sorted(list(self._sweep_args.items()), key=lambda x: x[0])
        arg_pairs = [[(name, arg) for arg in args]
                     for name, args in sorted_items]
        for i, prod in enumerate(itertools.product(*arg_pairs)):
            prod_dict = dict(prod)
            enum_dict = dict([(name, f(i)) for name, f in self._enum_funcs.items()])
            combined_dict = {**prod_dict, **enum_dict}
            if all(f(combined_dict) for f in self._filters):
                yield combined_dict


def process_kw_value_pair(
        kw: str,
        value: str
) -> str:
    if isinstance(value, bool):
        return f'--{kw}' if value else ''
    else:
        return f'--{kw}={value}'


def kwargs_to_str(kwargs: Kwargs) -> str:
    return ' '.join(process_kw_value_pair(name, kwarg) for name, kwarg in kwargs.items())


def build_run_file(
        sweep: Sweep,
        machine_addresses: List[str],
        experiment_base_dir: str,
        shared_data_dir: str,
        venv_name: str,
        username: str,
        required_ram: int,
        required_gpu_ram: Optional[int],
        pythonpath: str,
        experiment_file: str,
) -> str:
    run_file_data = {
        'machine_addresses': machine_addresses,
        'experiment_base_dir': experiment_base_dir,
        'data_dir': shared_data_dir,
        'venv_name': venv_name,
        'username': username
    }
    xid = int(time.time())
    # set up data directory for experiment.
    experiment_data_dir = os.path.join(shared_data_dir, str(xid))
    if os.path.isdir(experiment_data_dir):
        raise Exception(f'Experiment directory already exists.')
    os.mkdir(experiment_data_dir)

    run_file_path = os.path.join(experiment_data_dir, 'run_file.pickle')

    sweep = sweep.copy()
    sweep.add_enumeration('run_idx', lambda i: i)
    sweep.add_enumeration('data_path', lambda i: os.path.join(shared_data_dir, str(i)))

    runs = []
    for kwargs in sweep:
        run = Run(
            required_ram=required_ram,
            required_gpu_ram=required_gpu_ram,
            data_dir=shared_data_dir,
            experiment_base_dir=experiment_base_dir,
            venv_name=venv_name,
            xid=xid,
            run_num=kwargs['run_idx'],
            pythonpath=pythonpath,
            experiment_file=experiment_file,
            experiment_arg_string=kwargs_to_str(kwargs),
            experiment_environ_vars='',
        )
        runs.append(run)
    run_file_data['runs'] = runs
    with open(run_file_path, 'wb') as f:
        pickle.dump(run_file_data, f)
    return run_file_path


def build_run_file_from_sweep_file(
        sweep_file_path: str
) -> str:
    with open(sweep_file_path, 'r') as f:
        txt = f.read()
    experiment_data = eval(txt)
    p = experiment_data['experiment_params']
    sweep = Sweep()
    for sweep_command in experiment_data['sweep']:
        eval("sweep." + sweep_command)
    return build_run_file(
        sweep,
        machine_addresses=p['machine_addresses'],
        experiment_base_dir=p['experiment_base_dir'],
        shared_data_dir=p['shared_data_dir'],
        venv_name=p['venv_name'],
        username=p['username'],
        required_ram=p['required_ram'],
        required_gpu_ram=p['required_gpu_ram'],
        pythonpath=p['pythonpath'],
        experiment_file=p['experiment_file']
    )

if __name__ == '__main__':
    run_file_path = build_run_file_from_sweep_file(sys.argv[1])
    print(run_file_path)