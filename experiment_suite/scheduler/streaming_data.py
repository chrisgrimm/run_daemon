import os

class StreamManager:

    def __init__(self, run_dir: str):
        self._progress_file = os.path.join(run_dir, 'progress.txt')
        self._spun_up_file = os.path.join(run_dir, 'spun_up.txt')
        self._stream_dir = os.path.join(run_dir, 'stream_data')

    def log(self, key: str, value: float) -> None:
        data_path = os.path.join(self._stream_dir, key+'.txt')
        with open(data_path, 'a') as f:
            f.write(f'{value}\n')

    def set_progress(self, progress: float) -> None:
        with open(self._progress_file, 'w') as f:
            f.write(str(progress))

    def mark_as_spun_up(self) -> None:
        with open(self._spun_up_file, 'w') as f:
            f.write(str(1))
