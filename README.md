[![CircleCI](https://circleci.com/gh/shagunsodhani/xplogger.svg?style=svg)](https://circleci.com/gh/shagunsodhani/xplogger)
![PyPI - License](https://img.shields.io/pypi/l/xplogger)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/xplogger)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![DOI](https://zenodo.org/badge/351860799.svg)](https://zenodo.org/badge/latestdoi/351860799)


# xplogger
Logging utility for ML experiments

### Why

People use different tools for logging experimental results - [Tensorboard](https://www.tensorflow.org/tensorboard), [Wandb](https://www.wandb.com/) etc to name a few. Working with different collaborators, I will have to switch my logging tool with each new project. So I made this simple tool that provides a common interface to logging results to different loggers.

### Installation

* `pip install "xplogger[all]"`

If you want to use only the filesystem logger, use `pip install "xplogger"`

**Install from source**

* `git clone git@github.com:shagunsodhani/xplogger.git`
* `cd xplogger`
* `pip install ".[all]"`

Alternatively, `pip install "git+https://git@github.com/shagunsodhani/xplogger.git@master#egg=xplogger[all]"`

If you want to use only the filesystem logger, use `pip install .` or `pip install "git+https://git@github.com/shagunsodhani/xplogger.git@master#egg=xplogger"`.

### Documentation

[https://shagunsodhani.github.io/xplogger](https://shagunsodhani.github.io/xplogger/)

### Use

* Make a `logbook_config`:

    ```
    import xplogger.logbook
    logbook_config = xplogger.logbook.make_config(
        logger_dir = <path to write logs>,
        wandb_config = <wandb config or None>,
        tensorboard_config = <tensorboard config or None>,
        mlflow_config = <mlflow config or None>)
    ```

    The API for `make_config` can be accessed [here](https://shagunsodhani.com/xplogger/pages/api/xplogger.html?highlight=make_config#xplogger.logbook.make_config).

* Make a `LogBook` instance:

    ```
    logbook = xplogger.logbook.LogBook(config = logbook_config)
    ```

* Use the `logbook` instance:

    ```
    log = {
        "epoch": 1,
        "loss": 0.1,
        "accuracy": 0.2
    }
    logbook.write_metric(log)
    ```
    The API for `write_metric` can be accessed [here](https://shagunsodhani.com/xplogger/pages/api/xplogger.html?highlight=write_metric#xplogger.logbook.LogBook.write_metric).

### Note

* If you are writing to wandb, the `log` must have a key called `step`. If your `log` already captures the `step` but as a different key (say `epoch`), you can pass the `wandb_key_map` argument (set as `{epoch: step}`). For more details, refer the documentation [here](https://shagunsodhani.com/xplogger/pages/api/xplogger.html?highlight=make_config#xplogger.logbook.make_config).

* If you are writing to mlflow, the `log` must have a key called `step`. If your `log` already captures the `step` but as a different key (say `epoch`), you can pass the `mlflow_key_map` argument (set as `{epoch: step}`). For more details, refer the documentation [here](https://shagunsodhani.com/xplogger/pages/api/xplogger.html?highlight=make_config#xplogger.logbook.make_config).

* If you are writing to tensorboard, the `log` must have a key called `main_tag` or `tag` which acts as the data Identifier and another key called `global_step`. These keys are described [here](https://tensorboardx.readthedocs.io/en/latest/tensorboard.html#tensorboardX.SummaryWriter.add_scalars). If your `log` already captures these values but as different key (say `mode` for `main_tag` and `epoch` for `global_step`), you can pass the `tensorboard_key_map` argument (set as `{mode: main_tag, epoch: global_step}`). For more details, refer the documentation [here](https://shagunsodhani.com/xplogger/pages/api/xplogger.html?highlight=make_config#xplogger.logbook.make_config).


### Dev Setup

* `pip install -e ".[dev]"`
* Install pre-commit hooks `pre-commit install`
* The code is linted using:
    * `black`
    * `flake8`
    * `mypy`
    * `isort`
* Tests can be run locally using `nox`

### Acknowledgements

* Config for `circleci`, `pre-commit`, `mypy` etc are borrowed/modified from [Hydra](https://github.com/facebookresearch/hydra)
