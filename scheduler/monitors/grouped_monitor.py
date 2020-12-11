from scheduler.monitors import monitor
from typing import List, Mapping

class GroupedMonitor(monitor.Monitor):

    def __init__(self, monitors: List[monitor.Monitor]):
        self._monitors = monitors

    def get_data(self) -> Mapping[str, float]:
        data = dict()
        for monitor in self._monitors:
            for key, value in monitor.get_data().items():
                if key in data:
                    raise Exception(f'Duplicate key "{key}" in monitor group.')
                data[key] = value
        return data
