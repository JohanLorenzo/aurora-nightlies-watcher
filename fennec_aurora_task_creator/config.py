import copy
import json
import logging
import os

from collections import defaultdict
from frozendict import frozendict

from fennec_aurora_task_creator.directories import PROJECT_DIRECTORY
from fennec_aurora_task_creator.exceptions import MissingConfigurationError

logger = logging.getLogger(__name__)

_configs = {}

DEFAULT_LOCATION = os.path.join(PROJECT_DIRECTORY, 'config.json')

KEYS_AND_DEFAULT_VALUES = (
    {'path': 'credentials/client_id', 'environment_key': 'TASKCLUSTER_CLIENT_ID'},
    {'path': 'credentials/access_token', 'environment_key': 'TASKCLUSTER_ACCESS_TOKEN'},

    {
        'path': 'architectures_to_watch',
        'environment_key': 'ARCHITECTURES_TO_WATCH',
        'default_value': {
            'x86': 'android-x86-opt',
            'armv7_v15': 'android-api-15-opt',
        },
        'is_flat': False
    },

    {'path': 'task/name', 'environment_key': 'TASK_NAME', 'default_value': 'Google Play Publisher'},
    {'path': 'task/description', 'environment_key': 'TASK_DESCRIPTION', 'default_value': 'Publishes Aurora builds to Google Play Store'},
    {'path': 'task/owner', 'environment_key': 'TASK_OWNER_EMAIL'},
    {'path': 'task/provisioner_id', 'environment_key': 'TASK_PROVISIONER_ID'},
    {'path': 'task/worker_type', 'environment_key': 'TASK_WORKER_TYPE'},
    {'path': 'task/scopes', 'environment_key': 'TASK_SCOPES', 'is_flat': False},
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
    {'path': 'pulse/queue', 'environment_key': 'PULSE_QUEUE_NAME', 'default_value': 'fennec-auroras-to-process'},
    {
        'path': 'pulse/exchanges',
        'environment_key': 'PULSE_EXCHANGES',
        'default_value': [{
            'path': "exchange/taskcluster-queue/v1/task-completed",
            'routing_keys': ["route.index.gecko.v2.mozilla-aurora.nightly.latest.mobile.#"]
        }],
        'is_flat': False
    },

    {'path': 'verbose', 'environment_key': 'VERBOSE_MODE', 'default_value': False},
)


def get_config(config_path=None):
    config_path = config_path or DEFAULT_LOCATION

    try:
        return _configs[config_path]
    except KeyError:
        config = _generate_config_from_environment_and_config_file_and_defaults(config_path)
        _configs[config_path] = config
        return config


def _generate_config_from_environment_and_config_file_and_defaults(config_path):
    logger.debug('Loading config file at "{}"'.format(config_path))

    try:
        config_from_json_file = _load_config(config_path)
    except FileNotFoundError:
        config_from_json_file = frozendict({})

    final_config = _generate_final_config_object(config_from_json_file)
    final_config = _recursively_transform_to_dict(final_config)
    return frozendict(final_config)


def _load_config(config_path):
    with open(config_path) as f:
        return frozendict(json.load(f))


def _recursively_transform_to_dict(recursive_dict):
    for key, value in recursive_dict.items():
        if isinstance(value, dict):
            recursive_dict[key] = _recursively_transform_to_dict(value)
    return dict(recursive_dict)


def _generate_final_config_object(config_from_json_file):
    target_config_dict = _recursive_defaultdict()

    for key_and_default_value in KEYS_AND_DEFAULT_VALUES:
        target_config_dict = _add_configuration(
            target_config_dict, config_from_json_file, path_string=key_and_default_value['path'],
            environment_key=key_and_default_value['environment_key'],
            default_value=key_and_default_value.get('default_value', None),
            is_flat=key_and_default_value.get('is_flat', True),
        )

    return target_config_dict


def _recursive_defaultdict():
    return defaultdict(_recursive_defaultdict)


def _add_configuration(target_config_dict, config_from_json_file, path_string, environment_key, default_value=None, is_flat=True):
    target_config_dict = copy.copy(target_config_dict)
    path_list = path_string.split('/')

    _set_dict_path(
        target_config_dict,
        path_list,
        _get_environment_or_config_or_default_value(
            config_from_json_file, path_list, environment_key, default_value=default_value, is_flat=is_flat
        )
    )
    return target_config_dict


def _get_environment_or_config_or_default_value(config_from_json_file, path_list, environment_key, default_value=None, is_flat=True):
    try:
        value = os.environ[environment_key]
        if not is_flat:
            value = json.loads(value)

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
