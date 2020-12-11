import libtmux
import os
import subprocess
from typing import List
import sys

'''
./data_dir
-- run_num/
-- -- stdout.txt : standard output
-- -- stderr.txt : standard error output
-- -- data.pickle : data returned at the end of the process
-- -- progress.txt : text file containing a single number representing progress, -1 for failure.
-- -- spun_up.txt : file with a bit telling indicating whether a job has started using the bulk of its resources.
-- -- stream_data/
-- -- -- loss1.txt : text file containing floats accumulated throughout a run.
-- -- -- loss2.txt : text file containing floats accumulated throughout a run.
'''


class RunWrapper:

    def __init__(
            self,
            data_dir: str,
            experiment_base_dir: str,
            venv_name: str,
            xid: int,
            run_num: int,
            pythonpath: str,
            experiment_file: str,
            experiment_arg_string: str,
            experiment_environ_vars: str,
    ):
        self._run_dir = data_dir
        self._experiment_base_dir = experiment_base_dir
        self._venv_name = venv_name
        self._xid = xid
        self._run_num = run_num
        self._experiment_file = experiment_file
        self._experiment_arg_string = experiment_arg_string
        self._environ_vars = [f'PYTHONPATH={pythonpath}' ] + self._process_environ_vars(experiment_environ_vars)

        run_dir = self._create_run_directory()
        self._populate_run_directory(run_dir)
        self._run_experiment(run_dir)

    def _process_environ_vars(self, environ_vars: str) -> List[str]:
        return ",".split(environ_vars)


    def _create_run_directory(self):
        experiment_path = os.path.join(self._run_dir, str(self._xid))
        if not os.path.isdir(experiment_path):
            raise Exception(f'Cannot find experiment directory.')
        run_path = os.path.join(experiment_path, str(self._run_num))
        if os.path.isdir(run_path):
            raise Exception(f'Run dir {run_path} already exists.')
        os.mkdir(run_path)
        return run_path

    def _populate_run_directory(self, run_dir: str) -> None:
        with open(os.path.join(run_dir, 'progress.txt'), 'w') as f:
            f.write(str(0.0))
        with open(os.path.join(run_dir, 'stdout.txt'), 'w') as _:
            pass
        with open(os.path.join(run_dir, 'stderr.txt'), 'w') as _:
            pass
        with open(os.path.join(run_dir, 'spun_up.txt'), 'w') as f:
            f.write(str(0))
        os.mkdir(os.path.join(run_dir, 'stream_data'))

    def _get_or_create_tmux_window(self):
        server = libtmux.Server()
        session = server.find_where({'session_name': str(self._xid)})
        if session is None:
            raise Exception(f'Could not find session.')
        window_name = f'({self._run_num})'
        windows = session.list_windows()
        for window in windows:
            if window.name == window_name:
                return window
        return session.new_window(attach=False, window_name=window_name)

    def _run_experiment(self, run_path: str):
        venv_path = os.path.join(self._experiment_base_dir, self._venv_name)
        venv_command = f'source {venv_path}/bin/activate'
        python_command = (f'python {os.path.join(self._experiment_base_dir, self._experiment_file)} '
                          f'{self._experiment_arg_string} ')
        env_vars = ' '.join(self._environ_vars)
        full_command = f'{env_vars} {venv_command}; {python_command}'
        out_file = os.path.join(run_path, 'stdout.txt')
        err_file = os.path.join(run_path, 'stderr.txt')
        stdout, stderr = None, None
        try:
            stdout = open(out_file, 'w')
            stderr = open(err_file, 'w')
            p = subprocess.Popen(full_command, shell=True, stdout=stdout, stderr=stderr)
            retcode = p.wait()
            # if the program fails write -1 to the progress logger.
            if retcode != 0:
                with open(os.path.join(run_path, 'progress.txt'), 'w') as f:
                    f.write(str(-1))
            else:
                with open(os.path.join(run_path, 'progress.txt'), 'w') as f:
                    f.write(str(1))
        finally:
            if stdout is not None:
                stdout.close()
            if stderr is not None:
                stderr.close()






if __name__ == '__main__':

    RunWrapper(
        data_dir=sys.argv[1],
        experiment_base_dir=sys.argv[2],
        venv_name=sys.argv[3],
        xid=sys.argv[4],
        run_num=sys.argv[5],
        pythonpath=sys.argv[6],
        experiment_file=sys.argv[7],
        experiment_arg_string=sys.argv[8],
        experiment_environ_vars=sys.argv[9],
    )




