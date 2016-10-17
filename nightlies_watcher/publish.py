import logging
import os
import re
import taskcluster

from datetime import datetime, timedelta

from nightlies_watcher import treeherder, hg_mozilla
from nightlies_watcher.directories import PROJECT_DIRECTORY
from nightlies_watcher.tc_queue import queue


logger = logging.getLogger(__name__)

FENNEC_AURORA_APK_REGEX = re.compile(r'public/build/fennec-\d+.0a2.en-US.android.+\.apk')


with open(os.path.join(PROJECT_DIRECTORY, 'source_url.txt')) as f:
    source_url = f.read().rstrip()


def publish(config, revision, tasks_data_per_architecture):
    hg_push_id = hg_mozilla.get_push_id(config['repository_to_watch'], revision)
    tasks_data_per_architecture = get_artifact_urls(tasks_data_per_architecture)

    task_payload = craft_task_data(config, revision, hg_push_id, tasks_data_per_architecture)
    created_task_id = taskcluster.slugId().decode('utf-8')

    result = queue.createTask(payload=task_payload, taskId=created_task_id)
    logger.info('Created task %s: %s', created_task_id, result)


def get_artifact_urls(tasks_data_per_architecture):
    return {
        architecture: {
            'task_id': data['task_id'],
            'artifact_url': craft_artifact_url(data['task_id']),
        }
        for architecture, data in tasks_data_per_architecture.items()
    }


def craft_artifact_url(task_id):
    latest_artifacts = queue.listLatestArtifacts(task_id)
    apk_artifacts = [
        artifact['name']
        for artifact in latest_artifacts['artifacts']
        if FENNEC_AURORA_APK_REGEX.match(artifact['name']) is not None
    ]

    logger.debug(apk_artifacts)
    if len(apk_artifacts) != 1:
        raise Exception('Not only one artifact matches the APK regex. Artifacts: {}'.format(apk_artifacts))

    return 'https://queue.taskcluster.net/v1/task/{}/artifacts/{}'.format(task_id, apk_artifacts[0])


def craft_task_data(config, revision, hg_push_id, tasks_data_per_architecture):
    curent_datetime = datetime.utcnow()
    apks = {architecture: data['artifact_url'] for architecture, data in tasks_data_per_architecture.items()}

    task_config = config['task']
    treeherder_config = task_config['treeherder']

    return {
        'created': curent_datetime,
        'deadline': curent_datetime + timedelta(hours=1),
        'dependencies': [data['task_id'] for _, data in tasks_data_per_architecture.items()],
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
        'routes': treeherder.get_routes(config['repository_to_watch'], revision, hg_push_id),
        'scopes': task_config['scopes'],
        'workerType': task_config['worker_type'],
    }
