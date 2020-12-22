import pickle
import os
import subprocess

def get_scheduler_path() -> str:
    return os.path.join(
        os.path.expanduser('~'),
        'scheduler')


def scheduler_is_loaded() -> bool:
    return os.path.isdir(get_scheduler_path())


def load_scheduler() -> None:
    scheduler_http = 'https://github.com/chrisgrimm/scheduler.git'
    p = subprocess.Popen(f'git clone {scheduler_http}', shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         executable='/bin/bash')
    err = p.stderr.read()
    if err:
        raise Exception(f'Failed to clone repo: "{err}".')


def update_scheduler() -> None:
    command = f'cd {get_scheduler_path()}; git stash; git pull'
    p = subprocess.Popen(command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         executable='/bin/bash')
    err = p.stderr.read()
    if err:
        raise Exception(f'Failed to update repo: "{err}".')


if __name__ == '__main__':
    if scheduler_is_loaded():
        update_scheduler()
    else:
        load_scheduler()
    print(pickle.dumps({}, 0).decode())

