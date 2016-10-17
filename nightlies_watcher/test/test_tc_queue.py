import pytest

from nightlies_watcher.tc_queue import fetch_task_definition, pluck_architecture, pluck_repository, pluck_revision, _queue, fetch_artifacts_list, create_task
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
    monkeypatch.setattr(_queue, 'task', lambda _: TASK_DEFINITION)
    assert fetch_task_definition('VRzn3vi6RvSNaKTaT5u83A') == TASK_DEFINITION


def test_fetch_artifacts_list(monkeypatch):
    artifacts = [{
        'contentType': 'application/json',
        'storageType': 's3',
        'name': 'public/build/buildbot_properties.json',
        'expires': '2017-10-14T09:07:47.161Z'
    }, {
        'contentType': 'application/octet-stream',
        'storageType': 's3',
        'name': 'public/build/fennec-51.0a2.en-US.android-arm.apk',
        'expires': '2017-10-14T08:57:10.154Z'
    }]

    monkeypatch.setattr(_queue, 'listLatestArtifacts', lambda _: {
        'artifacts': artifacts,
    })
    assert fetch_artifacts_list('VRzn3vi6RvSNaKTaT5u83A') == artifacts


def test_create_task(monkeypatch):
    created_task_data = {
        'status': {
            'provisionerId': 'dummy-provisioner',
            'taskGroupId': 'LBrUAO8NRDmFbv5JMrm3vQ',
            'state': 'pending',
            'workerType': 'dummy-worker',
            'retriesLeft': 0,
            'schedulerId': '-',
            'taskId': 'LBrUAO8NRDmFbv5JMrm3vQ',
            'deadline': '2016-10-17T17:43:47.961Z',
            'expires': '2017-10-17T17:43:47.961Z',
            'runs': [
                {'scheduled': '2016-10-17T16:43:49.669Z', 'state': 'pending', 'reasonCreated': 'scheduled', 'runId': 0}
            ],
        },
    }

    monkeypatch.setattr(_queue, 'createTask', lambda payload, taskId: created_task_data)
    assert create_task(payload={}, task_id='LBrUAO8NRDmFbv5JMrm3vQ') == created_task_data
