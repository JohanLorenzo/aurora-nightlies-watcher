import json
import os
import pytest
import tempfile

from copy import copy, deepcopy
from frozendict import frozendict

from fennec_aurora_task_creator.config import get_config, _generate_final_config_object, _recursive_defaultdict, _add_configuration, \
    _get_environment_or_config_or_default_value, _generate_config_from_environment_and_config_file_and_defaults
from fennec_aurora_task_creator.exceptions import MissingConfigurationError


MINIMAL_REQUIRED_CONFIG = {
    'credentials': {
        'client_id': 'dummy-client-id',
        'access_token': 'dummy-token'
    },
    'task': {
        'owner': 'r@m.c',
        'provisioner_id': 'dummy-provisioner',
        'worker_type': 'dummy-worker',
        'scopes': [],
        'treeherder': {
            'symbol': 'dum',
            'reason': 'Dummy reason',
        }
    },
    'pulse': {
        'user': 'dummy-user',
        'password': 'dummy-password',
        'queue': 'dummy-queue'
    }
}

DEFAULT_PROVIDED_CONFIG = {
    'architectures_to_watch': {
        'x86': 'android-x86-opt',
        'armv7_v15': 'android-api-15-opt',
    },
    'taskcluster_index_pattern': 'gecko.v2.{repository}.revision.{revision}.mobile-l10n.{architecture}.multi',
    'task': {
        'name': 'Google Play Publisher',
        'description': 'Publishes Aurora builds to Google Play Store',
        'google_play_track': 'alpha',
        'treeherder': {
            'platform': 'Android',
            'group_name': 'Publisher',
            'group_symbol': 'pub',
            'tier': 3,
            'is_opt': True,
        },
    },
    'pulse': {
        'host': 'pulse.mozilla.org',
        'port': 5671,
        'exchanges': [{
            'path': 'exchange/taskcluster-queue/v1/task-completed',
            'routing_keys': [
                'route.index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-api-15-opt.multi',
                'route.index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-x86-opt.multi',
            ]
        }],
    },
    'verbose': False,
}


def merge(a, b, path=None):
    path = [] if path is None else path

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
        else:
            a[key] = b[key]
    return a


def test_get_config():
    with tempfile.TemporaryDirectory() as directory:
        config_path = os.path.join(directory, 'config.json')

        with open(config_path, 'w') as f:
            json.dump(MINIMAL_REQUIRED_CONFIG, f)

        config = get_config(config_path=config_path)
        expected_config = merge(deepcopy(MINIMAL_REQUIRED_CONFIG), DEFAULT_PROVIDED_CONFIG)

        assert config == expected_config
        assert isinstance(config, frozendict)

    # Second call doesn't reload file
    second_config = get_config(config_path=config_path)
    assert second_config is config


def test_generate_config_from_environment_and_config_file_and_defaults_accepts_no_config_file():
    # Set required configuration
    os.environ['TASKCLUSTER_CLIENT_ID'] = 'env-client-id'
    os.environ['TASKCLUSTER_ACCESS_TOKEN'] = 'env-token'
    os.environ['TASK_OWNER_EMAIL'] = 'env@m.c'
    os.environ['TASK_PROVISIONER_ID'] = 'env-prov-id'
    os.environ['TASK_WORKER_TYPE'] = 'env-worker-type'
    os.environ['TASK_SCOPES'] = '["env:scope"]'
    os.environ['TREEHERDER_JOB_SYMBOL'] = 'env'
    os.environ['TREEHERDER_JOB_REASON'] = 'env reason'
    os.environ['PULSE_USER'] = 'env-user'
    os.environ['PULSE_PASSWORD'] = 'env-password'
    os.environ['PULSE_QUEUE_NAME'] = 'env-queue'

    config = _generate_config_from_environment_and_config_file_and_defaults('/non/existing/path')
    assert config['credentials']['client_id'] == 'env-client-id'

    # Clean up
    del os.environ['TASKCLUSTER_CLIENT_ID']
    del os.environ['TASKCLUSTER_ACCESS_TOKEN']
    del os.environ['TASK_OWNER_EMAIL']
    del os.environ['TASK_PROVISIONER_ID']
    del os.environ['TASK_WORKER_TYPE']
    del os.environ['TASK_SCOPES']
    del os.environ['TREEHERDER_JOB_SYMBOL']
    del os.environ['TREEHERDER_JOB_REASON']
    del os.environ['PULSE_USER']
    del os.environ['PULSE_PASSWORD']
    del os.environ['PULSE_QUEUE_NAME']


def test_generate_final_config_object_allows_full_config_to_be_a_dict_alone():
    final_config = _generate_final_config_object(MINIMAL_REQUIRED_CONFIG)
    assert final_config['credentials']['access_token'] == 'dummy-token'


def test_generate_final_config_object_fulfills_default_values():
    final_config = _generate_final_config_object(MINIMAL_REQUIRED_CONFIG)

    assert final_config['architectures_to_watch'] == {
        'x86': 'android-x86-opt',
        'armv7_v15': 'android-api-15-opt',
    }

    assert final_config['task']['name'] == 'Google Play Publisher'
    assert final_config['task']['description'] == 'Publishes Aurora builds to Google Play Store'
    assert final_config['task']['google_play_track'] == 'alpha'

    assert final_config['task']['treeherder']['platform'] == 'Android'
    assert final_config['task']['treeherder']['group_name'] == 'Publisher'
    assert final_config['task']['treeherder']['group_symbol'] == 'pub'
    assert final_config['task']['treeherder']['tier'] == 3
    assert final_config['task']['treeherder']['is_opt']

    assert final_config['pulse']['host'] == 'pulse.mozilla.org'
    assert final_config['pulse']['port'] == 5671
    assert final_config['pulse']['exchanges'] == [{
        'path': 'exchange/taskcluster-queue/v1/task-completed',
        'routing_keys': [
            'route.index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-api-15-opt.multi',
            'route.index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-x86-opt.multi'
        ],
    }]

    assert not(final_config['verbose'])


def test_generate_final_config_object_allows_environment_variables():
    os.environ['TASKCLUSTER_ACCESS_TOKEN'] = 'dummy-env-token'

    final_config = _generate_final_config_object(MINIMAL_REQUIRED_CONFIG)
    assert final_config['credentials']['access_token'] == 'dummy-env-token'

    del os.environ['TASKCLUSTER_ACCESS_TOKEN']


def test_generate_final_config_parses_json_for_certain_keys():
    os.environ['TASK_SCOPES'] = '["project:releng:googleplay:aurora"]'

    final_config = _generate_final_config_object(MINIMAL_REQUIRED_CONFIG)
    assert final_config['task']['scopes'] == ["project:releng:googleplay:aurora"]

    del os.environ['TASK_SCOPES']


def test_generate_final_config_object_reports_missing_mandatory_configuration():
    initial_config = copy(MINIMAL_REQUIRED_CONFIG)
    del initial_config['credentials']['access_token']

    with pytest.raises(MissingConfigurationError):
        _generate_final_config_object(initial_config)


def test_recursive_default_dict():
    recursive_dict = _recursive_defaultdict()
    recursive_dict['does']['not']['throw']['an']['error'] = 'random value'


def test_add_configuration_does_not_modify_input_dict():
    target_dict = _recursive_defaultdict()
    target_dict2 = _add_configuration(target_dict, {}, 'many/keys', 'MANY_KEYS', default_value='value')
    assert target_dict2['many']['keys'] == 'value'
    assert target_dict['many']['keys'] == {}


def test_get_environment_or_config_or_default_value():
    path_list = ('many', 'keys')
    env_key = 'MANY_KEYS'

    config_json = {}
    with pytest.raises(MissingConfigurationError):
        _get_environment_or_config_or_default_value(config_json, path_list, env_key)

    default_value = 'defaut_value'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) == \
        'defaut_value'

    config_json['many'] = {'keys': 'json_value'}
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) == \
        'json_value'

    os.environ['MANY_KEYS'] = 'environment_value'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) == \
        'environment_value'
    del os.environ['MANY_KEYS']


def test_get_environment_or_config_or_default_value_supports_boolean_values():
    path_list = ('boolean_attribute',)
    env_key = 'BOOLEAN_ATTRIBUTE'
    default_value = True

    config_json = {}
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) is True

    config_json['boolean_attribute'] = 'True'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) is True

    os.environ['BOOLEAN_ATTRIBUTE'] = 'true'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) is True

    os.environ['BOOLEAN_ATTRIBUTE'] = 'OFF'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) is False

    os.environ['BOOLEAN_ATTRIBUTE'] = '0'
    assert _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value) is False

    os.environ['BOOLEAN_ATTRIBUTE'] = ''
    with pytest.raises(ValueError):
        _get_environment_or_config_or_default_value(config_json, path_list, env_key, default_value)

    del os.environ['BOOLEAN_ATTRIBUTE']
