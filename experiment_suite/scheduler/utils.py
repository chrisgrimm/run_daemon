import socket
from contextlib import closing
from dataclasses import dataclass
from typing import Optional
import os
import paramiko


@dataclass
class Run:
    required_ram: int
    required_gpu_ram: Optional[int]
    data_dir: str
    venv_name: str
    xid: int
    run_num: int
    pythonpath: str
    experiment_file: str
    experiment_arg_string: str
    experiment_environ_vars: str


def get_hostname() -> str:
    with open('/etc/hostname', 'r') as f:
        return f.read().strip()


