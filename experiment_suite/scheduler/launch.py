import argparse
import os
import re
import tempfile
from enum import Enum
from typing import Tuple, List, Union

from typing.io import TextIO

from experiment_suite.scheduler import run_scheduler
from experiment_suite import const
import io

class ArgType(Enum):
    PARSER = 0
    ENVIRON = 1


def get_from_parser_or_environ(
        args: argparse.Namespace,
        parser_key: str,
        environ_key: str
) -> Tuple[ArgType, str]:
    if parser_key not in args.__dict__:
        try:
            environ_var = os.environ[environ_key]
            return ArgType.ENVIRON, environ_var
        except KeyError:
            raise Exception(f'If optional --{parser_key} argument is not specified '
                            f'then {environ_key} environment variable must be defined.')
    else:
        return ArgType.PARSER, args.__dict__[parser_key]


def get_active_tmux_sessions(
        client: run_scheduler.ClientWrapper,
) -> List[str]:
    _, stdout, stderr = client.exec_command('tmux ls')
    if err := stderr.read():
        raise Exception(f'Failed to execute "tmux ls" with error message: {err}.')
    names = []
    for line in stdout.readlines():
        if m := re.match(r'^(\S?)\: .+$', line):
            names.append(m.groups()[0])
    return names


def launch_tmux_named_session_with_command(
        client: run_scheduler.ClientWrapper,
        session_name: str,
        command: str
) -> None:
    tmux_sessions = get_active_tmux_sessions(client)
    if session_name in tmux_sessions:
        raise Exception('Launcher session already exists.')

    client.exec_command(f'tmux -d -s "{session_name}" {command}')


def move_file_to_client(
        sweep_file_or_path: Union[str, io.TextIOBase],
        dest_path: str,
) -> None:
    if isinstance(sweep_file_or_path, io.TextIOBase):
        sweep_file_contents = sweep_file_or_path.read()
    else:
        with open(sweep_file_or_path, 'r') as f:
            sweep_file_contents = f.read()
    escaped_sweep_contents = sweep_file_contents.replace('"', r'\"')
    client.exec_command(f'echo "{escaped_sweep_contents}" > {dest_path}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-sweep_file', type=str, required=True)
    parser.add_argument('--machines', type=str)
    parser.add_argument('--user', type=str)

    args = parser.parse_args()
    machine_arg_type, machine_arg = get_from_parser_or_environ(args, 'machines', 'MACHINES')
    user_arg_type, user_arg = get_from_parser_or_environ(args, 'user', 'USER')

    split_by = lambda t: ':' if t is ArgType.ENVIRON else ','
    machine_addresses = machine_arg.split(split_by(machine_arg_type))
    users = user_arg.split(split_by(user_arg_type))

    if len(users) == 1:
        # If only one user is specified, use it for all machines.
        users = [users[0]] * len(machine_addresses)
    else:
        if len(users) != len(machine_addresses):
            raise Exception(f'If multiple users are specified, there must be a '
                            'one-to-one correspondence between users and machine '
                            f'addresses. Found {len(users)} users and '
                            f'{len(machine_addresses)} machines addresses.')

    # load clients
    addrs_and_clients = []
    client_lookup = dict()
    user_plus_addrs = []
    for user, addr in zip(users, machine_addresses):
        try:
            client = run_scheduler.ParamikoClient(user, addr, timeout=10)
            addrs_and_clients.append((addr, client))
            user_plus_addrs.append(f'{user}@{addr}')
            client_lookup[addr] = client
        except TimeoutError:
            pass
    data = run_scheduler.execute_across_machines('get_monitor_data',
                                                 args=[],
                                                 machines=addrs_and_clients)
    selected_addr, selected_client = None, None
    for addr, monitor_data in data.items():
        insufficient_mem = monitor_data['free_mem'] < 10 * const.GB
        insufficient_cpu = monitor_data['idle_cpu'] < 10
        if insufficient_cpu or insufficient_mem:
            selected_client = client_lookup[addr]
            selected_addr = addr
    if selected_client is None or selected_addr is None:
        raise Exception('Could not find client with sufficient resources among:\n' +
                        '\n'.join([f'\t[{addr}]' for addr in machine_addresses]))

    temp_name = tempfile.gettempprefix()
    # move the sweep file onto the machine in a temporary location.
    move_file_to_client(args.sweep_file, f'/tmp/sweep_{temp_name}.py')
    machine_string = '\n'.join(user_plus_addrs)
    move_file_to_client(io.StringIO(machine_string), f'/tmp/machines_{temp_name}')

    # execute the sweep_file --> run_file conversion remotely
    out = run_scheduler.execute_across_machines('sweep_file_to_run_file',
                                                args=[temp_name],
                                                machines=[(selected_addr, selected_client)])
    experiment_dir = out[selected_addr]['experiment_data_dir']
    xid = int(os.path.dirname(experiment_dir))
    # kick off the scheduler with the newly generated runfile.
    run_file = os.path.join(experiment_dir, 'run_file.pickle')
    command = (
        f'pip3.8 install --upgrade -i https://test.pypi.org/simple/ crgrimm-scheduler; '
        f'python3.8 -m experiment_suite.scheduler.run_scheduler schedule {run_file}')

    launch_tmux_named_session_with_command(selected_client, f"launcher-{xid}", command)
