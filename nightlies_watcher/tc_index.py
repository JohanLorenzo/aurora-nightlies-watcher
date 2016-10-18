from taskcluster import Index, exceptions

from nightlies_watcher.exceptions import TaskNotFoundError

_index = Index()


def get_task_id(repository, revision, android_architecture):
    namespace = _craft_full_namespace(repository, revision, android_architecture)

    try:
        task = _index.findTask(namespace)
        return task['taskId']
    except exceptions.TaskclusterRestFailure as e:
        if e.status_code == 404:
            raise TaskNotFoundError(repository, revision, android_architecture)
        raise


def _craft_full_namespace(repository, revision, android_architecture):
    return 'gecko.v2.{repository}.nightly.revision.{revision}.mobile.{architecture}'.format(
        repository=repository, revision=revision, architecture=android_architecture
    )
