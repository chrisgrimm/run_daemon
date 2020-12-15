from typing import Mapping
from experiment_suite.scheduler.monitors import monitor
import nvgpu


class GPUMonitor(monitor.Monitor):

    def get_data(self) -> Mapping[str, float]:
        info = nvgpu.gpu_info()
        data = dict()
        M = 1024 ** 2
        for entry in info:
            mem_free = (entry['mem_total'] - entry['mem_used']) * M
            data[f'gpu{entry["index"]}-mem-free'] = mem_free
        return data