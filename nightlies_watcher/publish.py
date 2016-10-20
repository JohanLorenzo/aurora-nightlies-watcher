import datetime
import logging
import os
import re
import taskcluster

from nightlies_watcher import treeherder, hg_mozilla, tc_index, tc_queue
from nightlies_watcher.directories import PROJECT_DIRECTORY
from nightlies_watcher.exceptions import NotOnlyOneApkError, TreeherderJobAlreadyExistError


logger = logging.getLogger(__name__)

FENNEC_AURORA_APK_REGEX = re.compile(r'^public/build/fennec-\d+.0a2.en-US.android.+\.apk$')


with open(os.path.join(PROJECT_DIRECTORY, 'source_url.txt')) as f:
    source_url = f.read().rstrip()


def publish_if_possible(config, repository, revision):
    task_config = config['task']
    job_name = task_config['name']

    if treeherder.does_job_already_exist(repository, revision, job_name, tier=task_config['treeherder']['tier']):
        raise TreeherderJobAlreadyExistError(repository, revision, job_name)

    tasks_data_per_architecture = _fetch_task_ids_per_achitecture(repository, revision, config['architectures_to_watch'])
    tasks_data_per_architecture = _fetch_artifacts(tasks_data_per_architecture)
    tasks_data_per_architecture = _filter_right_artifacts(tasks_data_per_architecture)
    tasks_data_per_architecture = _craft_artifact_urls(tasks_data_per_architecture)

    hg_push_id = hg_mozilla.get_push_id(repository, revision)
    task_payload = _craft_task_data(config, repository, revision, hg_push_id, tasks_data_per_architecture)

    created_task_id = taskcluster.slugId().decode('utf-8')
    result = tc_queue.create_task(task_payload, created_task_id)
    logger.info('Created task %s: %s', created_task_id, result)


def _fetch_task_ids_per_achitecture(repository, target_revision, android_architectures_definition):
    return {
        pusk_apk_architecture_name: {
            'task_id': tc_index.get_task_id(repository, target_revision, tc_namespace_architecture_name)
        }
        for pusk_apk_architecture_name, tc_namespace_architecture_name
        in android_architectures_definition.items()
    }


def _fetch_artifacts(tasks_data_per_architecture):
    return {
        architecture: {
            'task_id': data['task_id'],
            'all_artifacts': tc_queue.fetch_artifacts_list(data['task_id']),
        }
        for architecture, data in tasks_data_per_architecture.items()
    }


def _filter_right_artifacts(tasks_data_per_architecture):
    return {
        architecture: {
            'task_id': data['task_id'],
            'target_artifact': _pick_valid_artifact(data),
        }
        for architecture, data in tasks_data_per_architecture.items()
    }


def _pick_valid_artifact(task_data):
    apk_artifacts = [
        artifact['name']
        for artifact in task_data['all_artifacts']
        if FENNEC_AURORA_APK_REGEX.match(artifact['name']) is not None
    ]

    logger.debug(apk_artifacts)
    if len(apk_artifacts) != 1:
        raise NotOnlyOneApkError(apk_artifacts)

    return apk_artifacts[0]


def _craft_artifact_urls(tasks_data_per_architecture):
    return {
        architecture: {
            'task_id': data['task_id'],
            'artifact_url': 'https://queue.taskcluster.net/v1/task/{}/artifacts/{}'.format(
                data['task_id'], data['target_artifact']
            ),
        }
        for architecture, data in tasks_data_per_architecture.items()
    }


def _craft_task_data(config, repository, revision, hg_push_id, tasks_data_per_architecture):
    curent_datetime = datetime.datetime.utcnow()
    apks = {architecture: data['artifact_url'] for architecture, data in tasks_data_per_architecture.items()}

    task_config = config['task']
    treeherder_config = task_config['treeherder']

    return {
        'created': curent_datetime,
        'deadline': curent_datetime + datetime.timedelta(hours=1),
        # Sorting dependencies has no value for Taskcluster, but it makes output deterministic (used by tests)
        'dependencies': sorted(data['task_id'] for data in tasks_data_per_architecture.values()),
        'extra': {
            'treeherder': {
                'reason': treeherder_config['reason'],
                'tier': treeherder_config['tier'],
                'groupName': treeherder_config['group_name'],
                'groupSymbol': treeherder_config['group_symbol'],
                'symbol': treeherder_config['symbol'],
                'collection': {
                    'opt': treeherder_config['is_opt']
                },
                'machine': {
                    'platform': treeherder_config['platform']
                },
            },
        },
        'metadata': {
            'name': task_config['name'],
            'description': task_config['description'],
            'owner': task_config['owner'],
            'source': source_url,
        },
        'payload': {
            'apks': apks,
            'google_play_track': task_config['google_play_track'],
        },
        'provisionerId': task_config['provisioner_id'],
        'requires': 'all-completed',
        # Number of retries is forced (aka not configurable), in order to make sure we don't push the same APK twice
        'retries': 0,
        'routes': treeherder.get_routes(repository, revision, hg_push_id),
        'scopes': task_config['scopes'],
        'workerType': task_config['worker_type'],
    }
