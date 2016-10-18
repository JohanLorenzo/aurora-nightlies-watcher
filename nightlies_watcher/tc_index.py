from taskcluster import Index

_index = Index()


def get_task_id(repository, revision, android_architecture):
    namespace = _craft_full_namespace(repository, revision, android_architecture)
    task = _index.findTask(namespace)
    return task['taskId']


def _craft_full_namespace(repository, revision, android_architecture):
    return 'gecko.v2.{repository}.nightly.revision.{revision}.mobile.{architecture}'.format(
        repository=repository, revision=revision, architecture=android_architecture
    )
