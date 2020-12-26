import pickle
import sys
from experiment_suite.scheduler import sweep as sweep_lib

if __name__ == '__main__':
    run_file_path = sweep_lib.build_run_file_from_sweep_file(sys.argv[1])
    out = {'experiment_data_dir': run_file_path}
    print(pickle.dumps(out, 0).decode())