import logging

from thclient import TreeherderClient

from fennec_aurora_task_creator.exceptions import NoTreeherderResultSetError, TooManyTreeherderResultSetsError


logger = logging.getLogger(__name__)

_client = TreeherderClient()


def does_job_already_exist(repository, revision, job_name, tier=1):
    resultsets = _client.get_resultsets(
        project=repository,
        revision=revision,
    )

    if len(resultsets) == 0:
        raise NoTreeherderResultSetError(repository, revision)
    elif len(resultsets) != 1:
        raise TooManyTreeherderResultSetsError(repository, revision)

    jobs = _client.get_jobs(repository, count=2000, result_set_id=resultsets[0]['id'], tier=tier)

    return _is_job_in_list(jobs, job_name)


def _is_job_in_list(jobs, expected_job_name):
    filtered_jobs = [job for job in jobs if job['job_type_name'] == expected_job_name]
    return len(filtered_jobs) > 0


def get_routes(repository, revision, hg_push_id):
    treeherder_top_route_routes = ('tc-treeherder', 'tc-treeherder-stage',)
    return [
        '{top_route}.v2.{repository}.{revision}.{hg_push_id}'.format(
            top_route=top_route, repository=repository,
            revision=revision, hg_push_id=hg_push_id
        )
        for top_route in treeherder_top_route_routes
    ]
