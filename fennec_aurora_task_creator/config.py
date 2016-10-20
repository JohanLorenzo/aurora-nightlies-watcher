import json
import logging
import os
from frozendict import frozendict

from fennec_aurora_task_creator.directories import PROJECT_DIRECTORY, DATA_DIRECTORY

logger = logging.getLogger(__name__)

_configs = {}

DEFAULT_LOCATION = os.path.join(PROJECT_DIRECTORY, 'config.json')
DEFAULT_CONFIG_LOCATION = os.path.join(DATA_DIRECTORY, 'config.default.json')


def get_config(config_path=None):
    config_path = config_path or DEFAULT_LOCATION

    try:
        return _configs[config_path]
    except KeyError:
        config = _get_config_from_file_or_default_one(config_path)
        _configs[config_path] = config
        return config


def _get_config_from_file_or_default_one(config_path):
    logger.debug('Loading config file at "{}"'.format(config_path))

    try:
        return _load_config(config_path)
    except FileNotFoundError:
        logger.warn('"{}" not found. Loading default config at: {}'.format(config_path, DEFAULT_CONFIG_LOCATION))
        return _load_config(DEFAULT_CONFIG_LOCATION)


def _load_config(config_path):
    with open(config_path) as f:
        return frozendict(json.load(f))
