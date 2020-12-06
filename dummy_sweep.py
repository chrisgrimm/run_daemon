dict(
    experiment_params=dict(
        pythonpath='.',
        experiment_file='experiments/fixed_phi_high_dim.py'
        experiment_base_dir='off_policy_models/',
        shared_data_dir='/shared/home/crgrimm/',

        pythonpath='.',
        venv_name='venv',
        username='crgrimm',

        required_ram=5*(1024**3),
        required_gpu_ram=None,

        machine_addresses=[
            'rldl7.eecs.umich.edu',
        ]
    ),

    sweep=[
        'add_product("seed", range(5))',
        'add_product("env_name", ["cartpole"])',
        'add_product("model_type", ["mle", "ve"])',
        'add_product("num_policy_samples", [1000])',
        'add_product("full_buffer_size", [10_000])',
        'add_product("num_train_steps_per_iteration", [1000, 10_000])',
        'add_product("num_iterations", [20])', # think about this one.
        'add_product("batch_size", [32])',
        'add_product("ve_num_batches_for_tabular_model", [100, 500])', # this one also could matter
        'add_product("reward_model_lr", [1e-4, 5e-5])',
        'add_product("eval_depth", [100])',
        'add_product("eval_samples", [5])',
        'add_product("model_hidden_size", [32])', # this does nothing when env is not image based
        'add_product("model_lr", [1e-4, 5e-5])',
        'add_product("num_aggr", [10, 20, 50, 100])',
        'add_filter(lambda d: d["reward_model_lr"] == d["model_lr"])'
    ]
)