import re

from taskcluster import Queue

from fennec_aurora_task_creator.exceptions import UnmatchedRouteError

_queue = Queue()

ANYTHING_BUT_DOT = '([^.]+)'


def fetch_task_definition(task_id):
    return _queue.task(task_id)


def fetch_artifacts_list(task_id):
    return _queue.listLatestArtifacts(task_id)['artifacts']


def create_task(payload, task_id):
    return _queue.createTask(payload=payload, taskId=task_id)


def pluck_repository(route_pattern, task_definition):
    return _match_field_in_routes(route_pattern, task_definition, 'repository', 1)


def pluck_revision(route_pattern, task_definition):
    return _match_field_in_routes(route_pattern, task_definition, 'revision', 2)


def _match_field_in_routes(route_pattern, task_definition, field_name, field_number):
    route_matcher = re.compile(_get_regex_pattern_from_string_pattern(route_pattern))

    matched_things = [
        route_matcher.match(route).group(field_number)
        for route in task_definition['routes']
        if route_matcher.match(route) is not None
    ]

    if len(matched_things) == 0:
        raise UnmatchedRouteError(field_name, task_definition)

    return matched_things[0]


def _get_regex_pattern_from_string_pattern(string_pattern):
    pattern = 'index.{}'.format(string_pattern)
    pattern = pattern.replace('.', '\.')
    return pattern.format(
        repository=ANYTHING_BUT_DOT, revision=ANYTHING_BUT_DOT, architecture=ANYTHING_BUT_DOT
    )
