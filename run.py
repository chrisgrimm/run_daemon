import itertools
import os
import time
import sys
import subprocess
from typing import List, Callable, Dict, Optional, Iterable, Tuple, Union, TypeVar

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

def get_commands(
        pythonpath: str,
        file_to_run: str,
        sweep: Sweep
) -> List[str]:
    commands = []
    for kwargs in sweep:
        arg_string = ' '.join(process_kw_value_pair(name, kwarg) for name, kwarg in kwargs.items())
        command = f'PYTHONPATH={pythonpath} XLA_PYTHON_CLIENT_PREALLOCATE=false python {file_to_run} {arg_string}'
        commands.append(command)
    return commands


def divide_list(
        lst: List[T],
        num_parts: int
) -> List[List[T]]:
    divided_lists = [[] for _ in range(num_parts)]
    for i, item in enumerate(lst):
        divided_lists[i % len(divided_lists)].append(item)
    divided_lists = [l for l in divided_lists if len(l) > 0]
    return divided_lists


def build_directory_creation_command(
        data_dir: str,
        sweep: Sweep
) -> List[str]:
    return ([f'mkdir {data_dir}'] +
            [f'mkdir {k["data_path"]}' for k in sweep])
            # [f'echo "0" > {k["progress-file"]}' for k in sweep])


def safe_replace(
        string: str,
        safe_replace_dict: Dict[str, str]
) -> str:
    for key, value in safe_replace_dict.items():
        string = string.replace(key, value)
    return string

def ensure_good_session_name(session_name):
    return session_name.replace('.', '')

def build_tmux_environment_command(
        experiment_unique_name : str,
        experiment_name: str,
        pre_run_layout: List[str],
        post_run_layout: List[str],
        pythonpath: str,
        experiment_file: str,
        data_path: str,
        machine_idx: int,
        num_machines: int,
        max_concurrent_per_machine: int,
        sweep: Sweep,
        venv_path: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    data_dir = os.path.join(data_path, experiment_unique_name)
    venv_path = os.path.join(venv_path or 'venv', 'bin', 'activate')
    sweep = sweep.copy()
    sweep.add_enumeration('run_idx', lambda i: i)
    sweep.add_enumeration('data_path', lambda i: os.path.join(data_dir, str(i)))
    sweep.add_filter(lambda k: k['run_idx'] % num_machines == machine_idx)

    safe_replace_dict = {
        '{data_path}': data_path,
        '{venv_path}': venv_path,
    }

    pre_run_layout = [safe_replace(x, safe_replace_dict) for x in pre_run_layout]
    post_run_layout = [safe_replace(x, safe_replace_dict) for x in post_run_layout]

    commands = get_commands(pythonpath, experiment_file, sweep)
    divided_commands = divide_list(commands, max_concurrent_per_machine)

    tmux_prerun_layout_command = "\; ".join(pre_run_layout) + '\; '
    tmux_postrun_layout_command = "\; ".join(post_run_layout) + '\; '
    tmux_command_stack = []
    session_name = ensure_good_session_name(experiment_name)
    for i, commands in enumerate(divided_commands):
        tmux_entry = (f"tmux new-session -s '{session_name}' \; " if i == 0 else
                      f"tmux attach -t '{session_name}' \; new-window \; ")
        combined_command = '; '.join(commands)
        combined_command = combined_command.replace("'", "\'")
        complete_command = (
                tmux_entry +
                tmux_prerun_layout_command +
                f"send-keys 'source {venv_path}' C-m \; " +
                f"send-keys '{combined_command}' C-m \; " +
                tmux_postrun_layout_command +
                "detach"
        )
        tmux_command_stack.append(complete_command)
    data_commands = build_directory_creation_command(data_dir, sweep)
    return data_commands, tmux_command_stack


def run_experiment(
        experiment_file: str,
        experiment_name: str,
) -> None:
    with open(experiment_file, 'r') as f:
        text = f.read()
    experiment_data = eval(text)
    params = experiment_data['experiment_params']
    tmux_prerun_setup = experiment_data['tmux_prerun']
    tmux_postrun_setup = experiment_data['tmux_postrun']
    sweep_commands = experiment_data['sweep']
    sweep = Sweep()
    for sweep_command in sweep_commands:
        eval("sweep." + sweep_command)

    unique_name = str(int(time.time()))

    data_commands, tmux_commands = build_tmux_environment_command(
        **params,
        experiment_name=experiment_name,
        experiment_unique_name=unique_name,
        pre_run_layout=tmux_prerun_setup,
        post_run_layout=tmux_postrun_setup,
        sweep=sweep
    )

    for command in data_commands:
        subprocess.run([command], shell=True, check=True, capture_output=True)



    with open(os.path.join(
            experiment_data['experiment_params']['data_path'],
            unique_name,
            'description.txt'), 'w') as f:
        f.write(experiment_name)


    for command in tmux_commands:
        subprocess.run([command], shell=True, check=True)



if __name__ == '__main__':
    exp_file = sys.argv[1]
    experiment_name = sys.argv[2]
    run_experiment(exp_file, experiment_name)

