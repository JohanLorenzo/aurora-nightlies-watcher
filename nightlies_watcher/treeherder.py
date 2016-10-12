import logging

from thclient import TreeherderClient
from nightlies_watcher.hg_mozilla import get_minimal_repository_name

logger = logging.getLogger(__name__)

client = TreeherderClient()


def does_job_already_exist(repository, revision):
    minimal_repo_name = get_minimal_repository_name(repository)

    resultsets = client.get_resultsets(
        project=minimal_repo_name,
        revision=revision,
    )

    if len(resultsets) == 0:
        raise Exception('No result found for revision {} in repository {}'.format(revision, repository))
    elif len(resultsets) != 1:
        raise Exception('More than 1 result matches revision {} in repository {}'.format(revision, repository))

    jobs = client.get_jobs(minimal_repo_name, count=10000, result_set_id=resultsets[0]['id'])

    return _is_job_in_list(jobs, 'Google Play Publisher')


def _is_job_in_list(jobs, expected_job_name):
    filtered_jobs = [job for job in jobs if job['job_type_name'] == expected_job_name]
    return len(filtered_jobs) > 0
