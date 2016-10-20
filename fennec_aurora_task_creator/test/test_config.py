import json
import os
import pytest
import tempfile

from copy import copy
from frozendict import frozendict

from fennec_aurora_task_creator.config import get_config, _generate_final_config_object, _recursive_defaultdict, _add_configuration, \
    _get_environment_or_config_or_default_value
from fennec_aurora_task_creator.directories import DATA_DIRECTORY
from fennec_aurora_task_creator.exceptions import MissingConfigurationError


def test_get_config():
    original_config = {'config_attribute': 'config_argument'}

    with tempfile.TemporaryDirectory() as directory:
        config_path = os.path.join(directory, 'config.json')

        with open(config_path, 'w') as f:
            json.dump(original_config, f)

        config = get_config(config_path=config_path)
        assert config == original_config
        assert isinstance(config, frozendict)

    # Second call doesn't reload file
    second_config = get_config(config_path=config_path)
    assert second_config is config

    # Non-exising config loads default one
    default_config = get_config(config_path='/non/existing/path')
    with open(os.path.join(DATA_DIRECTORY, 'config.default.json')) as f:
        expected_default_config = json.load(f)

    assert default_config == expected_default_config


MINIMAL_CONFIG = {
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


def test_generate_final_config_object_allows_full_config_to_be_a_dict_alone():
    final_config = _generate_final_config_object(MINIMAL_CONFIG)
    assert final_config['credentials']['access_token'] == 'dummy-token'


def test_generate_final_config_object_fulfills_default_values():
    final_config = _generate_final_config_object(MINIMAL_CONFIG)

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

    assert not(final_config['verbose'])


def test_generate_final_config_object_allows_environment_variables():
    os.environ['TASKCLUSTER_ACCESS_TOKEN'] = 'dummy-env-token'

    final_config = _generate_final_config_object(MINIMAL_CONFIG)
    assert final_config['credentials']['access_token'] == 'dummy-env-token'

    del os.environ['TASKCLUSTER_ACCESS_TOKEN']


def test_generate_final_config_object_reports_missing_mandatory_configuration():
    initial_config = copy(MINIMAL_CONFIG)
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
