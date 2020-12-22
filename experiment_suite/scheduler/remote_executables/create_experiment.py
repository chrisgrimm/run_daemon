import pickle
import os
import sys
import subprocess


def create_project_folder(
        base_dir: str,
        xid: int,
        run_num: int
) -> str:
    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    folder_path = os.path.join(base_dir, f'{xid}_{run_num}')
    if os.path.isdir(folder_path):
        raise Exception('Folder path already exists.')
    os.mkdir(folder_path)
    return folder_path


def download_git_contents(
        project_folder: str,
        github_ssh_link: str,
) -> None:
    p = subprocess.Popen(f'cd {project_folder}; git clone {github_ssh_link}',
                         shell=True, executable='/bin/bash', stderr=subprocess.PIPE)
    if err := p.stderr.read():
        raise Exception(f'Failed to load github project with error: {err}.')


def create_venv(
        project_folder: str,
        python_command: str,
) -> None:
    command = (f'cd {project_folder}; {python_command} -m venv venv; '
               'source venv/bin/activate; pip install -r requirements.txt')
    p = subprocess.Popen(command, shell=True, executable='/bin/bash', stderr=subprocess.PIPE)
    if err := p.stderr.read():
        raise Exception(f'Failed to create virtual environment with error: {err}.')





if __name__ == '__main__':
    base_dir = sys.argv[1]
    xid = sys.argv[2]
    run_num = sys.argv[3]
    github_ssh_link = sys.argv[4]

    project_folder = create_project_folder(base_dir, int(xid), int(run_num))
    download_git_contents(project_folder, github_ssh_link)
    create_venv(project_folder, 'python3.8')
    print(pickle.dumps({'experiment_dir': project_folder}, 0).decode())
