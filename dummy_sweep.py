dict(
    experiment_params=dict(
        pythonpath='.',
        experiment_file='test_run.py',
        experiment_base_dir='~/run_daemon/',
        shared_data_dir='/shared/home/crgrimm/',

        venv_name='venv',
        username='crgrimm',

        required_ram=5*(1024**3),
        required_gpu_ram=None,

        machine_addresses=[
            'rldl7.eecs.umich.edu',
        ]
    ),

    sweep=[
        'add_product("to_add", [1, 2, 3])',
    ]
)
