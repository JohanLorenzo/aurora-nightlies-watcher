import pytest

from fennec_aurora_task_creator.tc_queue import fetch_task_definition, pluck_repository, pluck_revision, \
    _queue, fetch_artifacts_list, create_task, _get_regex_pattern_from_string_pattern
from fennec_aurora_task_creator.exceptions import UnmatchedRouteError

ROUTE_PATTERN = 'gecko.v2.{repository}.signed-nightly.nightly.revision.{revision}.mobile.{architecture}'

TASK_DEFINITION = {
    'routes': [
        'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.latest.mobile.android-x86-opt',
        'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.2017.02.10.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-x86-opt',
        'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.2017.02.10.latest.mobile.android-x86-opt',
        'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-x86-opt',
        'index.gecko.v2.mozilla-aurora.signed-nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile-l10n.android-x86-opt.en-US',
        'index.gecko.v2.mozilla-aurora.signed-nightly.pushdate.2017.02.10.20170210084116.mobile-l10n.android-x86-opt.en-US',
        'index.gecko.v2.mozilla-aurora.signed-nightly.latest.mobile-l10n.android-x86-opt.en-US',
        'index.project.releng.funsize.level-3.mozilla-aurora',
        'tc-treeherder.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.0',
        'tc-treeherder-stage.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.0',
    ]
}


def test_pluck_repository():
    assert pluck_repository(ROUTE_PATTERN, TASK_DEFINITION) == 'mozilla-aurora'

    with pytest.raises(UnmatchedRouteError):
        # Not signed signed-nightly
        pluck_repository(ROUTE_PATTERN, {
            'routes': ['index.gecko.v2.mozilla-aurora.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile-l10n.android-api-15']
        })


def test_pluck_revision():
    assert pluck_revision(ROUTE_PATTERN, TASK_DEFINITION) == '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99'

    with pytest.raises(UnmatchedRouteError):
        # No revision
        pluck_repository(ROUTE_PATTERN, {
            'routes': ['index.gecko.v2.mozilla-aurora.latest.mobile-l10n.android-api-15-opt.multi']
        })


def test_get_regex_pattern_from_string_pattern():
    assert _get_regex_pattern_from_string_pattern(ROUTE_PATTERN) == \
        r'index\.gecko\.v2\.([^.]+)\.signed-nightly\.nightly\.revision\.([^.]+)\.mobile\.([^.]+)'


def test_fetch_task_definition(monkeypatch):
    monkeypatch.setattr(_queue, 'task', lambda _: TASK_DEFINITION)
    assert fetch_task_definition('Klg1GnM4TAqeBqgz-FOdtw') == TASK_DEFINITION


def test_fetch_artifacts_list(monkeypatch):
    artifacts = [{
        'storageType': 's3',
        'name': 'public/build/en-US/target.apk',
        'expires': '2017-02-24T09:35:26.674Z',
        'contentType': 'application/binary',
    }, {
        'storageType': 's3',
        'name': 'public/build/target.apk',
        'expires': '2017-02-24T09:35:26.683Z',
        'contentType': 'application/binary',
    }]

    monkeypatch.setattr(_queue, 'listLatestArtifacts', lambda _: {
        'artifacts': artifacts,
    })
    assert fetch_artifacts_list('Klg1GnM4TAqeBqgz-FOdtw') == artifacts


def test_create_task(monkeypatch):
    created_task_data = {
        'status': {
            'taskId': 'Klg1GnM4TAqeBqgz-FOdtw',
            'provisionerId': 'scriptworker-prov-v1',
            'workerType': 'signing-linux-v1',
            'schedulerId': 'gecko-level-3',
            'taskGroupId': 'GZItMiWuRbaAy5W4WgpwjQ',
            'deadline': '2017-02-11T08:41:28.419Z',
            'expires': '2018-02-10T08:41:28.419Z',
            'retriesLeft': 5,
            'state': 'completed',
            'runs': [{
                'runId': 0,
                'state': 'completed',
                'reasonCreated': 'scheduled',
                'reasonResolved': 'completed',
                'workerGroup': 'signing-linux-v1',
                'workerId': 'signing-linux-4',
                'takenUntil': '2017-02-10T09:54:56.358Z',
                'scheduled': '2017-02-10T09:34:52.833Z',
                'started': '2017-02-10T09:34:56.446Z',
                'resolved': '2017-02-10T09:35:29.971Z',
            }]
        }
    }

    monkeypatch.setattr(_queue, 'createTask', lambda payload, taskId: created_task_data)
    assert create_task(payload={}, task_id='Klg1GnM4TAqeBqgz-FOdtw') == created_task_data
