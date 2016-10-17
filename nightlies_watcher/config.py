import json
import logging
import os
from frozendict import frozendict

from nightlies_watcher.directories import PROJECT_DIRECTORY

logger = logging.getLogger(__name__)

CONFIGS = {}


def get_config(path=None):
    config_path = path or os.path.join(PROJECT_DIRECTORY, 'config.json')

    try:
        return CONFIGS[config_path]
    except KeyError:
        logger.debug('Loading config file at "{}"'.format(config_path))

        with open(config_path) as f:
            config = frozendict(json.load(f))

        CONFIGS[config_path] = config
        return config
