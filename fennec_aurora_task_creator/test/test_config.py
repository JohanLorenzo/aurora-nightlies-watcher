import json
import os
import tempfile

from frozendict import frozendict

from fennec_aurora_task_creator.config import get_config
from fennec_aurora_task_creator.directories import DATA_DIRECTORY


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
