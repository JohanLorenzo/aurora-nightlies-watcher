import json
import logging
import os
import re
import taskcluster
import time

from nightlies_watcher import treeherder
from nightlies_watcher.tc_index import get_latest_task_id
from nightlies_watcher.tc_queue import get_revision


logger = logging.getLogger(__name__)

FENNEC_AURORA_APK_REGEX = re.compile(r'public/build/fennec-\d+.0a2.en-US.android.+\.apk')

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')

with open(os.path.join(PROJECT_DIRECTORY, 'source_url.txt')) as f:
    source_url = f.read().rstrip()


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
        run_if_new_builds_are_present(config)
        time.sleep(config['watch_interval_in_seconds'])


def run_if_new_builds_are_present(config):
    repository = config['repository_to_watch']

    logger.debug('Check if new builds are available')
    latest_task_definitions_per_achitecture = get_latest_task_definitions_per_achitecture(
        repository, config['architectures_to_watch']
    )
    logger.debug('Found these tasks: %s', latest_task_definitions_per_achitecture)

    try:
        revision = get_matching_revision(latest_task_definitions_per_achitecture)
    except:
        logger.warn('Some of the tasks are not defined against the same revision', latest_task_definitions_per_achitecture)
        return

    if treeherder.does_job_already_exist(
        repository, revision, job_name=config['task']['name'], tier=config['task']['treeherder']['tier']
    ):
        logger.info('Nothing to publish', latest_task_definitions_per_achitecture)
    else:
        logger.info('New builds found, starting publishing: %s', latest_task_definitions_per_achitecture)
        publish(config, revision, latest_task_definitions_per_achitecture)


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
    revisions = [task['revision'] for task in tasks_per_architecture.values()]
    if not revisions:
        raise Exception('No tasks given')

    first_revision_to_compare_to = revisions[0]
    if (all(revision == first_revision_to_compare_to for revision in revisions)):
        return first_revision_to_compare_to
    else:
        raise Exception('Not all tasks are defined against the same revision')


main(__name__)
