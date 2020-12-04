from typing import Optional, List
from utils import Run
import pickle

def peek(run_file: str) -> Optional[Run]:
    with open(run_file, 'rb') as f:
        runs: List[Run] = pickle.load(f)['runs']
    if len(runs) == 0:
        return None
    head, *tail = runs
    return head


def pop(run_file: str) -> Optional[Run]:
    with open(run_file, 'rb') as f:
        run_file_data = pickle.load(f)
    runs = run_file_data['runs']
    if len(runs) == 0:
        return None
    head, *tail = runs
    with open(run_file, 'wb') as f:
        run_file_data['runs'] = tail
        pickle.dump(run_file_data, f)
    return head