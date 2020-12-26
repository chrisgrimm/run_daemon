import pickle
import sys
from experiment_suite.scheduler import sweep as sweep_lib

if __name__ == '__main__':
    temp_name = sys.argv[1]
    sweep_file = f'/tmp/sweep_{temp_name}.py'
    machine_file = f'/tmp/machines_{temp_name}'
    run_file_path = sweep_lib.build_run_file_from_sweep_file(sweep_file, machine_file)
    out = {'experiment_data_dir': run_file_path}
    print(pickle.dumps(out, 0).decode())