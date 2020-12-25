import argparse
import os
from enum import Enum
from typing import Tuple
import pickle
from experiment_suite.scheduler import sweep as sweep_lib
from experiment_suite.scheduler import run_scheduler


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
    clients = []
    for user, addr in zip(users, machine_addresses):
        clients.append(run_scheduler.ParamikoClient(user, addr))
    # figure out which machine to use as a client (available resources)
    # spin up a tmux instance on that machine and start the client in it.
    sweep_lib.build_run_file_from_sweep_file(args.sweep_file)







