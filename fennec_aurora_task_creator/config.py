import copy
import json
import logging
import os

from collections import defaultdict
from frozendict import frozendict

from fennec_aurora_task_creator.directories import PROJECT_DIRECTORY, DATA_DIRECTORY
from fennec_aurora_task_creator.exceptions import MissingConfigurationError

logger = logging.getLogger(__name__)

_configs = {}

DEFAULT_LOCATION = os.path.join(PROJECT_DIRECTORY, 'config.json')
DEFAULT_CONFIG_LOCATION = os.path.join(DATA_DIRECTORY, 'config.default.json')

KEYS_AND_DEFAULT_VALUES = (
    {'path': 'credentials/client_id', 'environment_key': 'TASKCLUSTER_CLIENT_ID'},
    {'path': 'credentials/access_token', 'environment_key': 'TASKCLUSTER_ACCESS_TOKEN'},

    {'path': 'task/name', 'environment_key': 'TASK_NAME', 'default_value': 'Google Play Publisher'},
    {'path': 'task/description', 'environment_key': 'TASK_DESCRIPTION', 'default_value': 'Publishes Aurora builds to Google Play Store'},
    {'path': 'task/owner', 'environment_key': 'TASK_OWNER_EMAIL'},
    {'path': 'task/provisioner_id', 'environment_key': 'TASK_PROVISIONER_ID'},
    {'path': 'task/worker_type', 'environment_key': 'TASK_WORKER_TYPE'},
    {'path': 'task/scopes', 'environment_key': 'TASK_SCOPES'},
    {'path': 'task/google_play_track', 'environment_key': 'TASK_GOOGLE_PLAY_TRACK', 'default_value': 'alpha'},

    {'path': 'task/treeherder/platform', 'environment_key': 'TREEHERDER_PLATFORM', 'default_value': 'Android'},
    {'path': 'task/treeherder/group_name', 'environment_key': 'TREEHERDER_GROUP_NAME', 'default_value': 'Publisher'},
    {'path': 'task/treeherder/group_symbol', 'environment_key': 'TREEHERDER_GROUP_SYMBOL', 'default_value': 'pub'},
    {'path': 'task/treeherder/symbol', 'environment_key': 'TREEHERDER_JOB_SYMBOL', 'default_value': 'gp'},
    {'path': 'task/treeherder/reason', 'environment_key': 'TREEHERDER_JOB_REASON'},
    {'path': 'task/treeherder/tier', 'environment_key': 'TREEHERDER_TIER', 'default_value': 3},
    {'path': 'task/treeherder/is_opt', 'environment_key': 'TREEHERDER_IS_OPT', 'default_value': True},

    {'path': 'pulse/host', 'environment_key': 'PULSE_HOST', 'default_value': 'pulse.mozilla.org'},
    {'path': 'pulse/port', 'environment_key': 'PULSE_PORT', 'default_value': 5671},
    {'path': 'pulse/user', 'environment_key': 'PULSE_USER'},
    {'path': 'pulse/password', 'environment_key': 'PULSE_PASSWORD'},
    {'path': 'pulse/queue', 'environment_key': 'PULSE_QUEUE_NAME'},
    {'path': 'verbose', 'environment_key': 'VERBOSE_MODE', 'default_value': False},
)


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


def _generate_final_config_object(config_from_json_file):
    target_config_dict = _recursive_defaultdict()

    for key_and_default_value in KEYS_AND_DEFAULT_VALUES:
        target_config_dict = _add_configuration(
            target_config_dict, config_from_json_file, path_string=key_and_default_value['path'],
            environment_key=key_and_default_value['environment_key'],
            default_value=key_and_default_value.get('default_value', None)
        )

    return target_config_dict


def _recursive_defaultdict():
    return defaultdict(_recursive_defaultdict)


def _add_configuration(target_config_dict, config_from_json_file, path_string, environment_key, default_value=None):
    target_config_dict = copy.copy(target_config_dict)
    path_list = path_string.split('/')

    _set_dict_path(
        target_config_dict,
        path_list,
        _get_environment_or_config_or_default_value(
            config_from_json_file, path_list, environment_key, default_value=default_value
        )
    )
    return target_config_dict


def _get_environment_or_config_or_default_value(config_from_json_file, path_list, environment_key, default_value=None):
    try:
        value = os.environ[environment_key]
    except KeyError:
        try:
            value = _get_dict_path(config_from_json_file, path_list)
        except KeyError:
            value = default_value

    if value is None:
        raise MissingConfigurationError(environment_key, '/'.join(path_list))
    return value


def _set_dict_path(recursive_dictionary, path_list, value):
    if len(path_list) == 1:
        recursive_dictionary[path_list[0]] = value
    else:
        _set_dict_path(recursive_dictionary[path_list[0]], path_list[1:], value)


def _get_dict_path(dictionary, path_list):
    return dictionary[path_list[0]] if len(path_list) == 1 else _get_dict_path(dictionary[path_list[0]], path_list[1:])
