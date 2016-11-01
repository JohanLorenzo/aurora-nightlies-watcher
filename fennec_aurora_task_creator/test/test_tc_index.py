import pytest
import taskcluster

from fennec_aurora_task_creator.exceptions import TaskNotFoundError
from fennec_aurora_task_creator.tc_index import get_task_id, _craft_full_namespace, _index


def test_craft_full_namespace():
    # Supports en-US only builds
    assert _craft_full_namespace(
        config={'taskcluster_index_pattern': 'gecko.v2.{repository}.nightly.revision.{revision}.mobile.{architecture}'},
        repository='mozilla-aurora',
        revision='7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8',
        android_architecture='android-api-15-opt'
    ) == 'gecko.v2.mozilla-aurora.nightly.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15-opt'

    # Supports multi-locale builds
    assert _craft_full_namespace(
        config={'taskcluster_index_pattern': 'gecko.v2.{repository}.revision.{revision}.mobile-l10n.{architecture}.multi'},
        repository='mozilla-aurora',
        revision='c683b0d41a52ffab980165b79b9c82590001354b',
        android_architecture='android-api-15-opt'
    ) == 'gecko.v2.mozilla-aurora.revision.c683b0d41a52ffab980165b79b9c82590001354b.mobile-l10n.android-api-15-opt.multi'


def test_get_task_id(monkeypatch):
    config = {
        'taskcluster_index_pattern': 'gecko.v2.{repository}.revision.{revision}.mobile-l10n.{architecture}.multi',
    }

    monkeypatch.setattr(
        _index, 'findTask',
        lambda namespace: {'taskId': 'cMu_aqFiTD-UJ5l2K1TaUw'} if namespace ==
        'gecko.v2.mozilla-aurora.revision.c683b0d41a52ffab980165b79b9c82590001354b.mobile-l10n.android-x86-opt.multi'
        else None
    )
    assert get_task_id(config, 'mozilla-aurora', 'c683b0d41a52ffab980165b79b9c82590001354b', 'android-x86-opt') == \
        'cMu_aqFiTD-UJ5l2K1TaUw'

    def not_found(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='not found', superExc=None, status_code=404)

    monkeypatch.setattr(_index, 'findTask', not_found)
    with pytest.raises(TaskNotFoundError):
        get_task_id(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b', 'android-x86-opt')

    # Other errors than 404 should not be filtered out
    def other_error(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='internal server error', superExc=None, status_code=500)

    monkeypatch.setattr(_index, 'findTask', other_error)
    with pytest.raises(taskcluster.exceptions.TaskclusterRestFailure):
        get_task_id(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b', 'android-x86-opt')
