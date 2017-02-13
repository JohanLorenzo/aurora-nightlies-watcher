import pytest
import taskcluster

from fennec_aurora_task_creator.exceptions import TaskNotFoundError
from fennec_aurora_task_creator.tc_index import get_task_id, _craft_full_namespace, _index


def test_craft_full_namespace():
    # Supports en-US only builds
    assert _craft_full_namespace(
        config={'taskcluster_index_pattern': 'gecko.v2.{repository}.signed-nightly.nightly.revision.{revision}.mobile.{architecture}'},
        repository='mozilla-aurora',
        revision='6b063631a7d3ffd5dc2b621852e4d8ac8758ef99',
        android_architecture='android-api-15-opt'
    ) == 'gecko.v2.mozilla-aurora.signed-nightly.nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-api-15-opt'


def test_get_task_id(monkeypatch):
    config = {
        'taskcluster_index_pattern': 'gecko.v2.{repository}.signed-nightly.nightly.revision.{revision}.mobile.{architecture}',
    }

    monkeypatch.setattr(
        _index, 'findTask',
        lambda namespace: {'taskId': 'Klg1GnM4TAqeBqgz-FOdtw'} if namespace ==
        'gecko.v2.mozilla-aurora.signed-nightly.nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-x86-opt'
        else None
    )
    assert get_task_id(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99', 'android-x86-opt') == \
        'Klg1GnM4TAqeBqgz-FOdtw'

    def not_found(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='not found', superExc=None, status_code=404)

    monkeypatch.setattr(_index, 'findTask', not_found)
    with pytest.raises(TaskNotFoundError):
        get_task_id(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99', 'android-x86-opt')

    # Other errors than 404 should not be filtered out
    def other_error(_):
        raise taskcluster.exceptions.TaskclusterRestFailure(msg='internal server error', superExc=None, status_code=500)

    monkeypatch.setattr(_index, 'findTask', other_error)
    with pytest.raises(taskcluster.exceptions.TaskclusterRestFailure):
        get_task_id(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99', 'android-x86-opt')
