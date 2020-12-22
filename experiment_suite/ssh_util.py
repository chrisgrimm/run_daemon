import paramiko
from typing import Union, List, Tuple
import os


def build_paramiko_client(
        user: str,
        machine_address: str
) -> Tuple[str, paramiko.SSHClient]:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            client.connect(machine_address, username=user)
            break
        except paramiko.ssh_exception.SSHException as e:
            print(e)
            print(f'({machine_address}) Trying again.')
        except TimeoutError:
            print('Timed out, trying again...')
    print(f'connected to {user}@{machine_address}')
    return machine_address, client


def build_paramiko_clients(
        user: Union[str, List[str]],
        machine_addresses: List[str],
) -> List[Tuple[str, paramiko.SSHClient]]:
    if isinstance(user, str):
        user_list = [user] * len(machine_addresses)
    else:
        assert len(machine_addresses) == len(user)
        user_list = user
    return [build_paramiko_client(user, addr)
            for user, addr in zip(user_list, machine_addresses)]

def ssh_run_command(
        name_and_client: Tuple[str, paramiko.SSHClient],
        command: str,
) -> str:
    name, client = name_and_client
    _, stdout, stderr = client.exec_command(command)
    error: str = stderr.read().decode()
    out: str = stdout.read().decode()
    if error:
        raise Exception(f'Failed to run {command} on {name}. Returned error: "{error}".')
    return out


def ssh_read_file(
        name_and_client: Tuple[str, paramiko.SSHClient],
        file_path: str
) -> str:
    return ssh_run_command(name_and_client, f'cat {file_path}')


def ssh_write_file(
        name_and_client: Tuple[str, paramiko.SSHClient],
        file_path: str,
        contents: str,
        append: bool = False,
) -> None:
    contents = contents.replace('"', r'\"')
    stream_op = '>>' if append else '>'
    ssh_run_command(name_and_client, f'echo "{contents}" {stream_op} {file_path}')



def get_all_public_ssh_keys(
        names_and_clients: List[Tuple[str, paramiko.SSHClient]],
) -> List[str]:
    return [ssh_read_file(name_and_client, '~/.ssh/id_rsa.pub')
            for name_and_client in names_and_clients]


def get_authorized_keys(
        name_and_client: Tuple[str, paramiko.SSHClient],
) -> List[str]:
    authorized_keys_text = ssh_read_file(name_and_client, '~/.ssh/authorized_keys')
    return authorized_keys_text.split('\n')

# TODO figure out permission errors on RLDLs.
def add_nonduplicate_keys(
        name_and_client: Tuple[str, paramiko.SSHClient],
        keys: List[str],
        make_backup: bool = True,
) -> None:
    if make_backup:
        ssh_run_command(name_and_client, 'cp ~/.ssh/authorized_keys ~/temp_authorized_keys')
    existing_keys = get_authorized_keys(name_and_client)
    existing_keys = [e for e in existing_keys if e.strip()]
    ssh_run_command(name_and_client, 'rm ~/.ssh/authorized_keys')
    ssh_run_command(name_and_client, 'touch ~/.ssh/authorized_keys')
    all_keys = set(keys).union(set(existing_keys))
    all_keys = list(all_keys)
    for key in all_keys:
        ssh_write_file(name_and_client, '~/.ssh/authorized_keys', key, append=True)


def get_public_key(
        name_and_client: Tuple[str, paramiko.SSHClient]
) -> str:
    return ssh_read_file(name_and_client, '~/.ssh/id_rsa.pub').strip()

# TODO figure out how to make an SSH key automatically.
def create_public_key(
        name_and_client: Tuple[str, paramiko.SSHClient]
) -> str:
    ssh_run_command(name_and_client)


if __name__ == '__main__':
    machine_numbers = [
        1,
        # 2,
        3,
        4,
        # 5,
        #6,
        7,
        # 8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
    ]
    machines = [f'rldl{i}.eecs.umich.edu' for i in machine_numbers]
    user = 'crgrimm'

    all_name_client_pairs = [build_paramiko_client(user, machine) for machine in machines]
    all_public_keys = [get_public_key(ncp) for ncp in all_name_client_pairs]
    with open(os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub'), 'r') as f:
        local_public_key = f.read().strip()
    all_public_keys.append(local_public_key)
    print(len(all_public_keys))
    for ncp in all_name_client_pairs:
        add_nonduplicate_keys(ncp, all_public_keys)





