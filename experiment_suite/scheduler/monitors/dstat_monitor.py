import subprocess
import re
from typing import List, Mapping, Tuple
from experiment_suite.scheduler.monitors import monitor


class DStatMonitor(monitor.Monitor):

    def _process_row(self, row: str) -> List[str]:
        values = re.split(r'\s+', row)
        return [x for x in values if x]

    def _to_numeric(self, x: str) -> float:
        unit_mult = {
            'B': 1,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
            'P': 1024**5,
        }
        if m := re.match(r'^([\d\.]+)([TGMKB])$', x):
            num, unit = m.groups()
            return float(num) * unit_mult[unit]
        elif m := re.match(r'^([\d\.]+)$', x):
            num, = m.groups()
            return float(num)
        else:
            raise Exception(f'Unable to parse "{x}" as numeric.')

    def _process_output(self, out: str) -> Tuple[Mapping[str, float], Mapping[str, float]]:
        lines = out.split('\n')
        cpu_mem_header, header, values = lines
        cpu_headers, mem_headers = [self._process_row(x) for x in header.split('|')]
        cpu_values, mem_values = [self._process_row(x) for x in values.split('|')]
        cpu_values = [self._to_numeric(x) for x in cpu_values]
        mem_values = [self._to_numeric(x) for x in mem_values]
        cpu_data = dict(zip(cpu_headers, cpu_values))
        mem_data = dict(zip(mem_headers, mem_values))
        return cpu_data, mem_data

    def get_data(self) -> Mapping[str, float]:
        process = subprocess.Popen(['dstat --noupdate -cm 1 0'],
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = process.communicate()
        cpu_data, mem_data = self._process_output(out)
        return {
            'idle_cpu': cpu_data['idl'],
            'free_mem': mem_data['free'],
        }