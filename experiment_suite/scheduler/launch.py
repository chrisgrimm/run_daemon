import argparse
import os
from enum import Enum
from typing import Tuple
import pickle
from experiment_suite.scheduler import sweep as sweep_lib
from experiment_suite.scheduler import run_scheduler
from experiment_suite import const
import paramiko


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

# TODO left off here.
def launch(client: run_scheduler.ClientWrapper):
    client.exec_command('tmux -S {')


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

    # (1) copy the current sweep file to its appropriate xid location
    # - might require generating the xid when launcher is called and passing it.
    # (2) run the sweep-to-run file script on the copied sweep file
    # (3) initialize the scheduler (ideally inside of a tmux instance for visibility)

    # load clients
    addrs_and_clients = []
    client_lookup = dict()
    for user, addr in zip(users, machine_addresses):
        try:
            client = run_scheduler.ParamikoClient(user, addr, timeout=10)
            addrs_and_clients.append((addr, client))
            client_lookup[addr] = client
        except TimeoutError:
            pass
    data = run_scheduler.execute_across_machines('get_monitor_data',
                                                 args=[],
                                                 machines=addrs_and_clients)
    selected_client = None
    for addr, monitor_data in data.items():
        insufficient_mem = monitor_data['free_mem'] < 10 * const.GB
        insufficient_cpu = monitor_data['idle_cpu'] < 10
        if insufficient_cpu or insufficient_mem:
            selected_client = client_lookup[addr]
    if selected_client is None:
        raise Exception('Could not find client with sufficient resources amoung:\n' +
                        '\n'.join([f'\t[{addr}]' for addr in machine_addresses]))



    # spin up a tmux instance on that machine and start the client in it.
    sweep_lib.build_run_file_from_sweep_file(args.sweep_file)







