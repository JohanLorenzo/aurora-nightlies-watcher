import json
import os
from frozendict import frozendict

from nightlies_watcher.directories import PROJECT_DIRECTORY

config = None


# TODO avoid loading file at each import
with open(os.path.join(PROJECT_DIRECTORY, 'config.json')) as f:
    config = frozendict(json.load(f))
