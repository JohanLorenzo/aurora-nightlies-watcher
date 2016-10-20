import pytest
import taskcluster

from fennec_aurora_task_creator.exceptions import TaskNotFoundError
from fennec_aurora_task_creator.tc_index import get_task_id, _craft_full_namespace, _index


def test_craft_full_namespace():
    assert _craft_full_namespace('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'android-api-15') == \
        'gecko.v2.mozilla-aurora.nightly.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15'


def test_get_task_id(monkeypatch):
    monkeypatch.setattr(_index, 'findTask', lambda _: {'taskId': 'VRzn3vi6RvSNaKTaT5u83A'})
    assert get_task_id('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'android-api-15') == \
        'VRzn3vi6RvSNaKTaT5u83A'

    def not_found(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='not found', superExc=None, status_code=404)

    monkeypatch.setattr(_index, 'findTask', not_found)
    with pytest.raises(TaskNotFoundError):
        get_task_id('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b', 'android-x86')

    # Other errors than 404 should not be filtered out
    def other_error(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='internal server error', superExc=None, status_code=500)

    monkeypatch.setattr(_index, 'findTask', other_error)
    with pytest.raises(taskcluster.exceptions.TaskclusterRestFailure):
        get_task_id('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b', 'android-x86')
