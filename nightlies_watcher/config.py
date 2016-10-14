import json
import os
from frozendict import frozendict

config = None

# TODO avoid duplication
CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')

# TODO avoid loading file at each import
with open(os.path.join(PROJECT_DIRECTORY, 'config.json')) as f:
    config = frozendict(json.load(f))
