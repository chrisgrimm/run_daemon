import time
from experiment_suite.scheduler.streaming_data import StreamManager
from experiment_suite.experiment_utils import hyperparams

def run_experiment(
        data_path: str,
        run_idx: int,
        to_add: int,
):

    manager = StreamManager(data_path)

    for i in range(10):
        time.sleep(5)
        manager.set_progress(0.1 * (i+1))
        if i == 5:
            manager.mark_as_spun_up()
        print('blah', i)
        manager.log('squares', i**2 + to_add)

if __name__ == '__main__':
    parser = hyperparams.build_parser_for_experiment(run_experiment)
    args = parser.parse_args()
    run_experiment(**args.__dict__)

