import logging

from thclient import TreeherderClient
from nightlies_watcher.hg_mozilla import get_minimal_repository_name

logger = logging.getLogger(__name__)

client = TreeherderClient()


def does_job_already_exist(repository, revision, job_name, tier=1):
    minimal_repo_name = get_minimal_repository_name(repository)

    resultsets = client.get_resultsets(
        project=minimal_repo_name,
        revision=revision,
    )

    if len(resultsets) == 0:
        raise Exception('No result found for revision {} in repository {}'.format(revision, repository))
    elif len(resultsets) != 1:
        raise Exception('More than 1 result matches revision {} in repository {}'.format(revision, repository))

    jobs = client.get_jobs(minimal_repo_name, count=2000, result_set_id=resultsets[0]['id'], tier=tier)

    return _is_job_in_list(jobs, job_name)


def _is_job_in_list(jobs, expected_job_name):
    filtered_jobs = [job for job in jobs if job['job_type_name'] == expected_job_name]
    return len(filtered_jobs) > 0


def get_routes(repository, revision, hg_push_id):
    treeherder_top_route_routes = ('tc-treeherder', 'tc-treeherder-stage',)
    return [
        '{top_route}.v2.{minimal_repo_name}.{revision}.{hg_push_id}'.format(
            top_route=top_route, minimal_repo_name=get_minimal_repository_name(repository),
            revision=revision, hg_push_id=hg_push_id
        )
        for top_route in treeherder_top_route_routes
    ]
