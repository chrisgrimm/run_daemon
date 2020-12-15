from typing import Dict, Any
import pickle


def store_data(
        data_dir: str,
        experiment_kwargs: Dict[str, Any],
        experiment_data: Any
):
    with open(f'{data_dir}/data.pickle', 'wb') as f:
        pickle.dump((experiment_kwargs, experiment_data), f)
