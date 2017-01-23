import datetime
import os
import pytest

from distutils.util import strtobool

from fennec_aurora_task_creator.exceptions import NoApkFoundError, MoreThanOneApkFoundError, TreeherderJobAlreadyExistError
from fennec_aurora_task_creator.publish import publish_if_possible, _filter_right_artifacts, _craft_artifact_urls, \
    _craft_task_data, _fetch_task_ids_per_achitecture, _fetch_artifacts


def test_filter_right_artifacts():
    data = {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'all_artifacts': [{
              'storageType': 's3',
              'name': 'public/build/en-US/target.apk',
              'expires': '2017-02-02T23:18:22.491Z',
              'contentType': 'application/binary'
            }, {
              'storageType': 's3',
              'name': 'public/build/target.apk',
              'expires': '2017-02-02T23:18:22.489Z',
              'contentType': 'application/binary'
            }, {
              'storageType': 's3',
              'name': 'public/chainOfTrust.json.asc',
              'expires': '2017-02-02T23:18:22.490Z',
              "contentType": 'application/binary'
            }, {
              'storageType': 's3',
              'name': 'public/logs/chain_of_trust.log',
              'expires': '2017-02-02T23:18:22.487Z',
              'contentType': 'text/plain'
            }, {
              'storageType': 's3',
              'name': 'public/logs/task_error.log',
              'expires': '2017-02-02T23:18:22.491Z',
              'contentType': 'text/plain'
            }, {
              'storageType': 's3',
              'name': 'public/logs/task_output.log',
              'expires': '2017-02-02T23:18:22.489Z',
              'contentType': 'text/plain'
            }],
        },

        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'all_artifacts': [{
              'storageType': 's3',
              'name': 'public/build/en-US/target.apk',
              'expires': '2017-02-02T23:11:29.842Z',
              'contentType': 'application/binary'
            }, {
              'storageType': 's3',
              'name': 'public/build/target.apk',
              'expires': '2017-02-02T23:11:29.840Z',
              'contentType': 'application/binary'
            }, {
              'storageType': "s3",
              'name': 'public/chainOfTrust.json.asc',
              'expires': '2017-02-02T23:11:29.841Z',
              'contentType': 'application/binary'
            }, {
              'storageType': 's3',
              'name': 'public/logs/chain_of_trust.log',
              'expires': '2017-02-02T23:11:29.837Z',
              'contentType': 'text/plain'
            }, {
              'storageType': 's3',
              'name': 'public/logs/task_error.log',
              'expires': '2017-02-02T23:11:29.842Z',
              'contentType': 'text/plain'
            }, {
              'storageType': 's3',
              'name': 'public/logs/task_output.log',
              'expires': '2017-02-02T23:11:29.839Z',
              'contentType': 'text/plain'
            }],
        },
    }

    assert _filter_right_artifacts(data) == {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'target_artifact': 'public/build/target.apk',
        },
        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'target_artifact': 'public/build/target.apk',
        },
    }

    with pytest.raises(MoreThanOneApkFoundError):
        _filter_right_artifacts({
            'x86': {
                'task_id': 'fake',
                'all_artifacts': [
                    {'name': 'public/build/target.apk'},
                    {'name': 'public/build/target.apk'},
                ],
            },
        })

    with pytest.raises(NoApkFoundError):
        _filter_right_artifacts({
            'x86': {
                'task_id': 'fake',
                'all_artifacts': [
                    {'name': 'public/build/target.exe'},
                    {'name': 'public/build/target.dmg'},
                ],
            },
        })


def test_craft_artifact_urls():
    data = {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'target_artifact': 'public/build/target.apk',
        },
        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'target_artifact': 'public/build/target.apk',
        },
    }

    assert _craft_artifact_urls(data) == {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/Klg1GnM4TAqeBqgz-FOdtw/artifacts/public/build/target.apk',
        },
        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/TYPNy9Q0QvSNiijBjGVdhA/artifacts/public/build/target.apk',
        },
    }


def test_craft_task_data(monkeypatch):
    UTC_NOW = datetime.datetime.utcnow()

    class frozen_datetime:
        @classmethod
        def utcnow(cls):
            return UTC_NOW

    monkeypatch.setattr(datetime, 'datetime', frozen_datetime)

    config = {
        'task': {
            'name': 'Google Play Publisher',
            'description': 'Publishes Aurora builds to Google Play Store',
            'owner': 'r@m.c',
            'treeherder': {
                'platform': 'Android',
                'group_name': 'Publisher',
                'group_symbol': 'pub',
                'symbol': 'gp',
                'reason': 'Because this is a test',
                'tier': 3,
                'is_opt': True
            },
            'provisioner_id': 'test-provisioner',
            'worker_type': 'test-worker',
            'scopes': ['project:releng:googleplay:aurora'],
            'dry_run': True,
            'google_play_track': 'alpha',
        },
    }

    tasks_data_per_architecture = {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/Klg1GnM4TAqeBqgz-FOdtw/artifacts/public/build/target.apk',
        },
        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/TYPNy9Q0QvSNiijBjGVdhA/artifacts/public/build/target.apk',
        },
    }

    assert _craft_task_data(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99', '10715', tasks_data_per_architecture) == {
        'created': UTC_NOW,
        'deadline': UTC_NOW + datetime.timedelta(hours=1),
        'dependencies': ['Klg1GnM4TAqeBqgz-FOdtw', 'TYPNy9Q0QvSNiijBjGVdhA'],
        'extra': {
            'treeherder': {
                'reason': 'Because this is a test',
                'tier': 3,
                'groupName': 'Publisher',
                'groupSymbol': 'pub',
                'symbol': 'gp',
                'collection': {
                    'opt': True
                },
                'machine': {
                    'platform': 'Android'
                },
            },
        },
        'metadata': {
            'name': 'Google Play Publisher',
            'description': 'Publishes Aurora builds to Google Play Store',
            'owner': 'r@m.c',
            'source': 'https://github.com/mozilla-releng/fennec-aurora-task-creator',
        },
        'payload': {
            'apks': {
                'x86': 'https://queue.taskcluster.net/v1/task/Klg1GnM4TAqeBqgz-FOdtw/artifacts/public/build/target.apk',
                'armv7_v15':  'https://queue.taskcluster.net/v1/task/TYPNy9Q0QvSNiijBjGVdhA/artifacts/public/build/target.apk',
            },
            'dry_run': True,
            'google_play_track': 'alpha',
        },
        'provisionerId': 'test-provisioner',
        'requires': 'all-completed',
        'retries': 0,
        'routes': [
            'tc-treeherder.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.10715',
            'tc-treeherder-stage.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.10715',
        ],
        'scopes': ['project:releng:googleplay:aurora'],
        'workerType': 'test-worker',
    }


def test_fetch_task_ids_per_achitecture(monkeypatch):
    from fennec_aurora_task_creator import tc_index

    monkeypatch.setattr(
        tc_index, 'get_task_id', lambda _, __, ___, architecture: 'Klg1GnM4TAqeBqgz-FOdtw' if architecture == 'android-x86' else 'TYPNy9Q0QvSNiijBjGVdhA'
    )

    config = {
        'architectures_to_watch': {
            'armv7_v15': 'android-api-15',
            'x86': 'android-x86',
        }
    }

    assert _fetch_task_ids_per_achitecture(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99') == {
        'x86': {'task_id': 'Klg1GnM4TAqeBqgz-FOdtw'},
        'armv7_v15': {'task_id': 'TYPNy9Q0QvSNiijBjGVdhA'},
    }


def test_fetch_artifacts(monkeypatch):
    from fennec_aurora_task_creator import tc_queue

    monkeypatch.setattr(tc_queue, 'fetch_artifacts_list', lambda _: ['dummy_data'])

    data = {
        'x86': {'task_id': 'Klg1GnM4TAqeBqgz-FOdtw'},
        'armv7_v15': {'task_id': 'TYPNy9Q0QvSNiijBjGVdhA'},
    }

    assert _fetch_artifacts(data) == {
        'x86': {
            'task_id': 'Klg1GnM4TAqeBqgz-FOdtw',
            'all_artifacts': ['dummy_data'],
        },
        'armv7_v15': {
            'task_id': 'TYPNy9Q0QvSNiijBjGVdhA',
            'all_artifacts': ['dummy_data'],
        },
    }


@pytest.mark.skipif(strtobool(os.environ.get('SKIP_NETWORK_TESTS', 'true')), reason='Tests requiring network are skipped')
def test_publish_if_possible(monkeypatch):
    config = {
        'task': {
            'name': 'Google Play Publisher',
            'description': 'Publishes Aurora builds to Google Play Store',
            'owner': 'r@m.c',
            'treeherder': {
                'platform': 'Android',
                'group_name': 'Publisher',
                'group_symbol': 'pub',
                'symbol': 'gp',
                'reason': 'Because this is a test',
                'tier': 3,
                'is_opt': True
            },
            'provisioner_id': 'test-provisioner',
            'worker_type': 'test-worker',
            'scopes': ['project:releng:googleplay:aurora'],
            'dry_run': True,
            'google_play_track': 'alpha',
        },
        'architectures_to_watch': {
          'x86': 'android-x86-opt',
          'armv7_v15': 'android-api-15-opt'
        },
        'taskcluster_index_pattern': 'gecko.v2.{repository}.signed-nightly.nightly.revision.{revision}.mobile.{architecture}',
    }

    UTC_NOW = datetime.datetime.utcnow()

    class frozen_datetime:
        @classmethod
        def utcnow(cls):
            return UTC_NOW

    monkeypatch.setattr(datetime, 'datetime', frozen_datetime)

    def assert_create_task_is_called_with_right_arguments(payload, _):
        assert payload == {
            'created': UTC_NOW,
            'deadline': UTC_NOW + datetime.timedelta(hours=1),
            'dependencies': ['Klg1GnM4TAqeBqgz-FOdtw', 'TYPNy9Q0QvSNiijBjGVdhA'],
            'extra': {
                'treeherder': {
                    'reason': 'Because this is a test',
                    'tier': 3,
                    'groupName': 'Publisher',
                    'groupSymbol': 'pub',
                    'symbol': 'gp',
                    'collection': {
                        'opt': True
                    },
                    'machine': {
                        'platform': 'Android'
                    },
                },
            },
            'metadata': {
                'name': 'Google Play Publisher',
                'description': 'Publishes Aurora builds to Google Play Store',
                'owner': 'r@m.c',
                'source': 'https://github.com/mozilla-releng/fennec-aurora-task-creator',
            },
            'payload': {
                'apks': {
                    'x86':       'https://queue.taskcluster.net/v1/task/Klg1GnM4TAqeBqgz-FOdtw/artifacts/public/build/target.apk',
                    'armv7_v15': 'https://queue.taskcluster.net/v1/task/TYPNy9Q0QvSNiijBjGVdhA/artifacts/public/build/target.apk',
                },
                'dry_run': True,
                'google_play_track': 'alpha',
            },
            'provisionerId': 'test-provisioner',
            'requires': 'all-completed',
            'retries': 0,
            'routes': [
                'tc-treeherder.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.10715',
                'tc-treeherder-stage.v2.mozilla-aurora.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.10715',
            ],
            'scopes': ['project:releng:googleplay:aurora'],
            'workerType': 'test-worker',
        }

    from fennec_aurora_task_creator import treeherder
    monkeypatch.setattr(treeherder, 'does_job_already_exist', lambda _, __, ___, tier: False)

    from fennec_aurora_task_creator import tc_queue
    monkeypatch.setattr(tc_queue, 'create_task', assert_create_task_is_called_with_right_arguments)

    publish_if_possible(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99')


def test_publish_raises_error_if_job_exists_in_treeherder(monkeypatch):
    config = {
        'task': {
            'name': 'Google Play Publisher',
            'treeherder': {
                'tier': 3,
            }
        }
    }

    from fennec_aurora_task_creator import treeherder
    monkeypatch.setattr(treeherder, 'does_job_already_exist', lambda _, __, ___, tier: True)

    with pytest.raises(TreeherderJobAlreadyExistError):
        publish_if_possible(config, 'mozilla-aurora', '6b063631a7d3ffd5dc2b621852e4d8ac8758ef99')
