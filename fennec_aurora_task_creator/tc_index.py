from taskcluster import Index, exceptions

from fennec_aurora_task_creator.exceptions import TaskNotFoundError

_index = Index()


def get_task_id(config, repository, revision, android_architecture):
    namespace = _craft_full_namespace(config, repository, revision, android_architecture)

    try:
        task = _index.findTask(namespace)
        return task['taskId']
    except exceptions.TaskclusterRestFailure as e:
        if e.status_code == 404:
            raise TaskNotFoundError(repository, revision, android_architecture)
        raise


def _craft_full_namespace(config, repository, revision, android_architecture):
    return config['taskcluster_index_pattern'].format(
        repository=repository, revision=revision, architecture=android_architecture
    )
