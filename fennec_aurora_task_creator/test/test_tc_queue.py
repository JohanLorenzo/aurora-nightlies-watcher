import pytest

from fennec_aurora_task_creator.tc_queue import fetch_task_definition, pluck_repository, pluck_revision, \
    _queue, fetch_artifacts_list, create_task, _get_regex_pattern_from_string_pattern
from fennec_aurora_task_creator.exceptions import UnmatchedRouteError

ROUTE_PATTERN = 'gecko.v2.{repository}.revision.{revision}.mobile-l10n.{architecture}.multi'

TASK_DEFINITION = {
    'routes': [
        'index.gecko.v2.mozilla-aurora.revision.d9cfe58247e85c05ad98a4e60045bbdd62e0ec2b.mobile-l10n.android-api-15-opt.multi',
        'index.gecko.v2.mozilla-aurora.pushdate.2016.11.08.20161108081244.mobile-l10n.android-api-15-opt.multi',
        'index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-api-15-opt.multi',
        'index.buildbot.branches.mozilla-aurora.android-api-15',
        'index.buildbot.revisions.d9cfe58247e85c05ad98a4e60045bbdd62e0ec2b.mozilla-aurora.android-api-15',
    ]
}


def test_pluck_repository():
    assert pluck_repository(ROUTE_PATTERN, TASK_DEFINITION) == 'mozilla-aurora'

    with pytest.raises(UnmatchedRouteError):
        # Not mobile-l10n
        pluck_repository(ROUTE_PATTERN, {
            'routes': ['index.gecko.v2.mozilla-aurora.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15']
        })


def test_pluck_revision():
    assert pluck_revision(ROUTE_PATTERN, TASK_DEFINITION) == 'd9cfe58247e85c05ad98a4e60045bbdd62e0ec2b'

    with pytest.raises(UnmatchedRouteError):
        # No revision
        pluck_repository(ROUTE_PATTERN, {
            'routes': ['index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-api-15-opt.multi']
        })


def test_get_regex_pattern_from_string_pattern():
    assert _get_regex_pattern_from_string_pattern(ROUTE_PATTERN) == \
        r'index\.gecko\.v2\.([^.]+)\.revision\.([^.]+)\.mobile-l10n\.([^.]+)\.multi'


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
