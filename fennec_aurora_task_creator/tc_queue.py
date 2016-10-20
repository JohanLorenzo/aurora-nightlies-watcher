import re

from taskcluster import Queue

from fennec_aurora_task_creator.exceptions import UnmatchedRouteError

_queue = Queue()

ROUTE_MATCHER = re.compile(r'index.gecko.v2.([^.]+).nightly.revision.([^.]+).mobile.([^.]+)')


def fetch_task_definition(task_id):
    return _queue.task(task_id)


def fetch_artifacts_list(task_id):
    return _queue.listLatestArtifacts(task_id)['artifacts']


def create_task(payload, task_id):
    return _queue.createTask(payload=payload, taskId=task_id)


def pluck_repository(task_definition):
    return _match_field_in_routes(task_definition, 'repository', 1)


def pluck_revision(task_definition):
    return _match_field_in_routes(task_definition, 'revision', 2)


def pluck_architecture(task_definition):
    return _match_field_in_routes(task_definition, 'architecture', 3)


def _match_field_in_routes(task_definition, field_name, field_number):
    matched_things = [
        ROUTE_MATCHER.match(route).group(field_number)
        for route in task_definition['routes']
        if ROUTE_MATCHER.match(route) is not None
    ]

    if len(matched_things) == 0:
        raise UnmatchedRouteError(field_name, task_definition)

    return matched_things[0]
