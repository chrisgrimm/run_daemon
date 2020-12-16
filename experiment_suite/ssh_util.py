import paramiko
from typing import Union, List


def build_paramiko_client(
        user: str,
        machine_address: str
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(machine_address, username=user)
    return client


def build_paramiko_clients(
        user: Union[str, List[str]],
        machine_addresses: List[str],
) -> List[paramiko.SSHClient]:
    if isinstance(user, str):
        user_list = [user] * len(machine_addresses)
    else:
        assert len(machine_addresses) == len(user)
        user_list = user
    return [build_paramiko_client(user, addr)
            for user, addr in zip(user_list, machine_addresses)]


def ssh_read_file(
        client: paramiko.SSHClient,
        file_path: str
) -> str:
    _, stdout, stderr = client.exec_command(f'cat {file_path}')
    error: str = stderr.read().decode()
    out: str = stdout.read().decode
    if error:
        raise Exception(f'Failed to read id_rsa.pub. Returned error: "{error}".')
    return out


def get_all_public_ssh_keys(
        clients: List[paramiko.SSHClient],
) -> List[str]:
    return [ssh_read_file(client, '~/.ssh/id_rsa.pub')
            for client in clients]


# TODO
def get_authorized_keys(
        user: str,
        machine_address: str,
) -> List[str]:
    pass


