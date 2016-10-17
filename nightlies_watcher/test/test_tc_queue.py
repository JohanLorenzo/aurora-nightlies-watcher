import pytest

from nightlies_watcher.tc_queue import fetch_task_definition, pluck_architecture, pluck_repository, pluck_revision, queue
from nightlies_watcher.exceptions import UnmatchedRouteError

TASK_DEFINITION = {
    'routes': [
        'index.gecko.v2.mozilla-aurora.nightly.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15',
    ]
}


def test_pluck_repository():
    assert pluck_repository(TASK_DEFINITION) == 'mozilla-aurora'

    with pytest.raises(UnmatchedRouteError):
        # Not nightly
        pluck_repository({
            'routes': ['index.gecko.v2.mozilla-aurora.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15']
        })


def test_pluck_revision():
    assert pluck_revision(TASK_DEFINITION) == '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8'

    with pytest.raises(UnmatchedRouteError):
        # No revision
        pluck_repository({
            'routes': ['index.gecko.v2.mozilla-aurora.latest.mobile.android-api-15']
        })


def test_pluck_architecture():
    assert pluck_architecture(TASK_DEFINITION) == 'android-api-15'

    with pytest.raises(UnmatchedRouteError):
        # Not mobile
        pluck_repository({
            'routes': ['index.gecko.v2.mozilla-aurora.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.firefox.win32']
        })


def test_fetch_task_definition(monkeypatch):
    monkeypatch.setattr(queue, 'task', lambda _: TASK_DEFINITION)
    assert fetch_task_definition('VRzn3vi6RvSNaKTaT5u83A') == TASK_DEFINITION
