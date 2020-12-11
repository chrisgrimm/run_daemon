from typing import Optional, List
from scheduler.utils import Run
import pickle
import os


def peek(run_file: str) -> Optional[Run]:
    with open(run_file, 'rb') as f:
        is_scheduled_and_run: List[(bool, Run)] = pickle.load(f)['runs']
    unscheduled_runs = [run for is_scheduled, run in is_scheduled_and_run
                        if not is_scheduled]
    if len(unscheduled_runs) == 0:
        return None
    return unscheduled_runs[0]


def pop(run_file: str) -> Optional[Run]:
    with open(run_file, 'rb') as f:
        run_file_data = pickle.load(f)
    is_scheduled_and_run: List[(bool, Run)] = run_file_data['runs']
    unscheduled_runs = [(idx, run) for idx, (is_scheduled, run) in enumerate(is_scheduled_and_run)
                        if not is_scheduled]
    if len(unscheduled_runs) == 0:
        return None
    idx, run = unscheduled_runs[0]
    run_file_data['runs'][idx] = (True, run)
    with open(run_file, 'wb') as f:
        pickle.dump(run_file_data, f)
    return run


def purge_if_empty(run_file: str) -> None:
    with open(run_file, 'rb') as f:
        is_scheduled_and_run = pickle.load(f)['runs']
    unscheduled_runs = [run for is_scheduled, run in is_scheduled_and_run
                        if not is_scheduled]
    if len(unscheduled_runs) == 0:
        os.remove(run_file)
