import pickle
from typing import Mapping, Any
import os
import sys


def get_info(run_path: str) -> Mapping[str, Any]:
    with open(os.path.join(run_path, 'progress.txt'), 'r') as f:
        progress = float(f.read())
    with open(os.path.join(run_path, 'spun_up.txt'), 'r') as f:
        is_spun_up = bool(int(f.read()))
    return {
        'progress': progress,
        'spun_up': is_spun_up
    }


def get_all_info(data_dir: str, xid: str) -> Mapping[str, Mapping[str, Any]]:
    xid_path = os.path.join(data_dir, xid)
    run_data = dict()
    for run in os.listdir(xid_path):
        if not run.isnumeric():
            continue
        run_path = os.path.join(xid_path, run)
        run_info = get_info(run_path)
        run_data[run] = run_info
    return run_data


if __name__ == '__main__':
    data_dir, xid = sys.argv[1], sys.argv[2]
    run_data = get_all_info(data_dir, xid)
    decoded = pickle.dumps(run_data, 0).decode()
    print(decoded)