import socket
from contextlib import closing
from dataclasses import dataclass
from typing import Optional

@dataclass
class Run:
    required_ram: int
    required_gpu_ram: Optional[int]
    data_dir: str
    experiment_base_dir: str
    venv_name: str
    xid: int
    run_num: int
    pythonpath: str
    experiment_file: str
    experiment_arg_string: str
    experiment_environ_vars: str
