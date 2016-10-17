import json
import os
import tempfile

from frozendict import frozendict

from nightlies_watcher.config import get_config


def test_get_config():
    original_config = {'config_attribute': 'config_argument'}

    with tempfile.TemporaryDirectory() as directory:
        config_path = os.path.join(directory, 'config.json')

        with open(config_path, 'w') as f:
            json.dump(original_config, f)

        config = get_config(path=config_path)
        assert config == original_config
        assert isinstance(config, frozendict)

    # Second call doesn't reload file
    second_config = get_config(path=config_path)
    assert second_config is config
