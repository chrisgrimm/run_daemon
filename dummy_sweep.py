dict(
    experiment_params=dict(
        pythonpath='.',
        experiment_file='test_run.py',
        experiments_dir='~/run_daemon/',
        shared_data_dir='/shared/home/crgrimm/',
        github_ssh_link='git@github.com:chrisgrimm/scheduler.git',
        venv_name='venv',
        required_ram=5*(1024**3),
        required_gpu_ram=None,
    ),

    sweep=[
        'add_product("to_add", [1, 2, 3])',
    ]
)
