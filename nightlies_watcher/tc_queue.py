import re

from taskcluster import Queue

queue = Queue()

REVISION_MATCHER = re.compile(r'index.gecko.v2.[^.]+.nightly.revision.([^.]+).mobile.[^.]+')


def get_revision(task_id):
    task_definition = queue.task(task_id)
    return _pluck_revision(task_definition)


def _pluck_revision(task_definition):
    matched_revisions = [
        REVISION_MATCHER.match(route).group(1)
        for route in task_definition['routes']
        if REVISION_MATCHER.match(route) is not None
    ]

    if len(matched_revisions) == 0:
        raise Exception('No revision was found in the routes of: {}'.format(task_definition))

    return matched_revisions[0]
