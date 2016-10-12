import json
import logging
import os
import re
import taskcluster
import time

from datetime import datetime, timedelta

from nightlies_watcher import treeherder
from nightlies_watcher.tc_index import get_latest_task_id
from nightlies_watcher.tc_queue import queue, get_revision


logger = logging.getLogger(__name__)

FENNEC_AURORA_APK_REGEX = re.compile(r'public/build/fennec-\d+.0a2.en-US.android.+\.apk')

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')


def main(name=None):
    if name not in ('__main__', None):
        return

    FORMAT = '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    with open(os.path.join(PROJECT_DIRECTORY, 'config.json')) as f:
        config = json.load(f)

    taskcluster.config['credentials']['clientId'] = config['credentials']['client_id']
    taskcluster.config['credentials']['accessToken'] = config['credentials']['access_token']

    while True:
        run_if_new_builds_are_present(config['repository_to_watch'], config['architectures_to_watch'])
        time.sleep(config['watch_interval_in_seconds'])


def run_if_new_builds_are_present(repository, android_architectures):
    logger.debug('Check if new builds are available')
    latest_task_definitions_per_achitecture = get_latest_task_definitions_per_achitecture(repository, android_architectures)
    logger.debug('Found these tasks: %s', latest_task_definitions_per_achitecture)

    try:
        revision = get_matching_revision(latest_task_definitions_per_achitecture)
    except:
        logger.warn('Some of the tasks are not defined against the same revision', latest_task_definitions_per_achitecture)
        return

    if treeherder.does_job_already_exist(repository, revision):
        logger.info('Nothing to publish', latest_task_definitions_per_achitecture)
    else:
        logger.info('New builds found, starting publishing: %s', latest_task_definitions_per_achitecture)
        publish(latest_task_definitions_per_achitecture)



def get_latest_task_definitions_per_achitecture(repository, android_architectures):
    task_ids_per_achitecture = {
        pusk_apk_architecture_name: {
            'task_id': get_latest_task_id(repository, namespace_architecture_name)
        }
        for pusk_apk_architecture_name, namespace_architecture_name
        in android_architectures.items()
    }

    return {
        architecture_name: {
            'task_id': data['task_id'],
            'revision': get_revision(data['task_id'])
        }
        for architecture_name, data
        in task_ids_per_achitecture.items()
    }


def get_matching_revision(tasks_per_architecture):
    revisions = [task['revision'] for _, task in tasks_per_architecture.items()]
    if len(revisions) == 0:
        raise Exception('No tasks given')

    first_revision_to_compare_to = revisions[0]
    if (all(revision == first_revision_to_compare_to for revision in revisions)):
        return first_revision_to_compare_to
    else:
        raise Exception('Not all tasks are defined against the same revision')


def have_all_tasks_never_been_published(task_ids_per_achitecture, last_published_task_ids_per_achitecture):
    return all(
        data['task_id'] != last_published_task_ids_per_achitecture[architecture]['task_id']
        for architecture, data in task_ids_per_achitecture.items()
    )


def publish(tasks_data_per_architecture):
    tasks_data_per_architecture = get_artifact_urls(tasks_data_per_architecture)
    task_payload = craft_task_data(tasks_data_per_architecture)
    created_task_id = taskcluster.slugId().decode('utf-8')
    result = queue.createTask(payload=task_payload, taskId=created_task_id)
    logger.debug('Created task %s: %s', created_task_id, result)


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
        raise Exception('EROOROR')

    return 'https://queue.taskcluster.net/v1/task/{}/artifacts/{}'.format(task_id, apk_artifacts[0])


def craft_task_data(tasks_data_per_architecture):
    curent_datetime = datetime.utcnow()
    apks = {architecture: data['artifact_url'] for architecture, data in tasks_data_per_architecture.items()}

    return {
        'created': curent_datetime,
        'deadline': curent_datetime + timedelta(hours=1),
        'dependencies': [data['task_id'] for _, data in tasks_data_per_architecture.items()],
        'extra': {},
        'metadata': {
            'name': 'Google Play Publisher',
            'description': 'Publishes Aurora builds to Google Play Store',
            'owner': 'release@mozilla.com',
            'source': 'https://github.com/JohanLorenzo/nightlies-watcher'
        },
        'payload': {
            'apks': apks,
            'google_play_track': 'alpha',
            'maxRunTime': 600
        },
        'provisionerId': 'scriptworker-prov-v1',
        'requires': 'all-completed',
        'retries': 0,
        'routes': [],
        'scopes': [
            'project:releng:googleplay:aurora'
        ],
        'workerType': 'pushapk-v1'
    }


main(__name__)
