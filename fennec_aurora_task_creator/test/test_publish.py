import datetime
import os
import pytest

from distutils.util import strtobool

from fennec_aurora_task_creator.exceptions import NotOnlyOneApkError, TreeherderJobAlreadyExistError
from fennec_aurora_task_creator.publish import publish_if_possible, _filter_right_artifacts, _craft_artifact_urls, \
    _craft_task_data, _fetch_task_ids_per_achitecture, _fetch_artifacts


def test_filter_right_artifacts():
    data = {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            # Real data contains way more artifacts
            'all_artifacts': [{
                'contentType': 'application/json',
                'storageType': 's3',
                'name': 'public/build/buildbot_properties.json',
                'expires': '2017-10-14T09:04:35.473Z',
            }, {
                'contentType': 'application/octet-stream',
                'storageType': 's3',
                'name': 'public/build/fennec-51.0a2.en-US.android-i386.apk',
                'expires': '2017-10-14T09:02:50.195Z',
            }, {
                'contentType': 'text/plain',
                'storageType': 's3',
                'name': 'public/build/fennec-51.0a2.en-US.android-i386.checksums.asc',
                'expires': '2017-10-14T09:04:13.407Z',
            }],
        },

        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
            'all_artifacts': [{
                'contentType': 'application/json',
                'storageType': 's3',
                'name': 'public/build/buildbot_properties.json',
                'expires': '2017-10-14T09:07:47.161Z'
            }, {
                'contentType': 'application/octet-stream',
                'storageType': 's3',
                'name': 'public/build/fennec-51.0a2.en-US.android-arm.apk',
                'expires': '2017-10-14T08:57:10.154Z'
            }, {
                'contentType': 'text/plain',
                'storageType': 's3',
                'name': 'public/build/fennec-51.0a2.en-US.android-arm.checksums.asc',
                'expires': '2017-10-14T09:07:26.275Z'
            }],
        },
    }

    assert _filter_right_artifacts(data) == {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            'target_artifact': 'public/build/fennec-51.0a2.en-US.android-i386.apk',
        },
        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
            'target_artifact': 'public/build/fennec-51.0a2.en-US.android-arm.apk',
        },
    }

    with pytest.raises(NotOnlyOneApkError):
        _filter_right_artifacts({
            'x86': {
                'task_id': 'fake',
                'all_artifacts': [
                    {'name': 'public/build/fennec-51.0a2.en-US.android-i386.apk'},
                    {'name': 'public/build/fennec-51.0a2.en-US.android-i386-2.apk'},
                ],
            },
        })

    with pytest.raises(NotOnlyOneApkError):
        _filter_right_artifacts({
            'x86': {
                'task_id': 'fake',
                'all_artifacts': [
                    {'name': 'public/build/firefox-51.0a2.en-US.win32.exe'},
                    {'name': 'public/build/fennec-51.0a1.en-US.android-i386.apk'},  # Nightly
                    {'name': 'public/build/fennec-51.0b1.en-US.android-i386.apk'},
                    {'name': 'public/build/fennec-51.0.en-US.android-i386.apk'},
                ],
            },
        })


def test_craft_artifact_urls():
    data = {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            'target_artifact': 'public/build/fennec-51.0a2.en-US.android-i386.apk',
        },
        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
            'target_artifact': 'public/build/fennec-51.0a2.en-US.android-arm.apk',
        },
    }

    assert _craft_artifact_urls(data) == {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/QbosbKzTTB2E08IHTAtTfw/artifacts/public/build/fennec-51.0a2.en-US.android-i386.apk',
        },
        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/VRzn3vi6RvSNaKTaT5u83A/artifacts/public/build/fennec-51.0a2.en-US.android-arm.apk',
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
            'google_play_track': 'alpha'
        },
    }

    tasks_data_per_architecture = {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/QbosbKzTTB2E08IHTAtTfw/artifacts/public/build/fennec-51.0a2.en-US.android-i386.apk',
        },
        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
            'artifact_url': 'https://queue.taskcluster.net/v1/task/VRzn3vi6RvSNaKTaT5u83A/artifacts/public/build/fennec-51.0a2.en-US.android-arm.apk',
        },
    }

    assert _craft_task_data(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', '10148', tasks_data_per_architecture) == {
        'created': UTC_NOW,
        'deadline': UTC_NOW + datetime.timedelta(hours=1),
        'dependencies': ['QbosbKzTTB2E08IHTAtTfw', 'VRzn3vi6RvSNaKTaT5u83A'],
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
                'x86': 'https://queue.taskcluster.net/v1/task/QbosbKzTTB2E08IHTAtTfw/artifacts/public/build/fennec-51.0a2.en-US.android-i386.apk',
                'armv7_v15':  'https://queue.taskcluster.net/v1/task/VRzn3vi6RvSNaKTaT5u83A/artifacts/public/build/fennec-51.0a2.en-US.android-arm.apk',
            },
            'google_play_track': 'alpha',
        },
        'provisionerId': 'test-provisioner',
        'requires': 'all-completed',
        'retries': 0,
        'routes': [
            'tc-treeherder.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
            'tc-treeherder-stage.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
        ],
        'scopes': ['project:releng:googleplay:aurora'],
        'workerType': 'test-worker',
    }


def test_fetch_task_ids_per_achitecture(monkeypatch):
    from fennec_aurora_task_creator import tc_index

    monkeypatch.setattr(
        tc_index, 'get_task_id', lambda _, __, ___, architecture: 'QbosbKzTTB2E08IHTAtTfw' if architecture == 'android-x86' else 'VRzn3vi6RvSNaKTaT5u83A'
    )

    config = {
        'architectures_to_watch': {
            'armv7_v15': 'android-api-15',
            'x86': 'android-x86',
        }
    }

    assert _fetch_task_ids_per_achitecture(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8') == {
        'x86': {'task_id': 'QbosbKzTTB2E08IHTAtTfw'},
        'armv7_v15': {'task_id': 'VRzn3vi6RvSNaKTaT5u83A'},
    }


def test_fetch_artifacts(monkeypatch):
    from fennec_aurora_task_creator import tc_queue

    monkeypatch.setattr(tc_queue, 'fetch_artifacts_list', lambda _: ['dummy_data'])

    data = {
        'x86': {'task_id': 'QbosbKzTTB2E08IHTAtTfw'},
        'armv7_v15': {'task_id': 'VRzn3vi6RvSNaKTaT5u83A'},
    }

    assert _fetch_artifacts(data) == {
        'x86': {
            'task_id': 'QbosbKzTTB2E08IHTAtTfw',
            'all_artifacts': ['dummy_data'],
        },
        'armv7_v15': {
            'task_id': 'VRzn3vi6RvSNaKTaT5u83A',
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
            'google_play_track': 'alpha'
        },
        'architectures_to_watch': {
          'x86': 'android-x86-opt',
          'armv7_v15': 'android-api-15-opt'
        },
        'taskcluster_index_pattern': 'gecko.v2.{repository}.nightly.revision.{revision}.mobile.{architecture}',
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
            'dependencies': ['QbosbKzTTB2E08IHTAtTfw', 'VRzn3vi6RvSNaKTaT5u83A'],
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
                    'x86': 'https://queue.taskcluster.net/v1/task/QbosbKzTTB2E08IHTAtTfw/artifacts/public/build/fennec-51.0a2.en-US.android-i386.apk',
                    'armv7_v15':  'https://queue.taskcluster.net/v1/task/VRzn3vi6RvSNaKTaT5u83A/artifacts/public/build/fennec-51.0a2.en-US.android-arm.apk',
                },
                'google_play_track': 'alpha',
            },
            'provisionerId': 'test-provisioner',
            'requires': 'all-completed',
            'retries': 0,
            'routes': [
                'tc-treeherder.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
                'tc-treeherder-stage.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
            ],
            'scopes': ['project:releng:googleplay:aurora'],
            'workerType': 'test-worker',
        }

    from fennec_aurora_task_creator import treeherder
    monkeypatch.setattr(treeherder, 'does_job_already_exist', lambda _, __, ___, tier: False)

    from fennec_aurora_task_creator import tc_queue
    monkeypatch.setattr(tc_queue, 'create_task', assert_create_task_is_called_with_right_arguments)

    publish_if_possible(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8')


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
        publish_if_possible(config, 'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8')
