from taskcluster import Index
from nightlies_watcher.hg_mozilla import get_minimal_repository_name

_index = Index()


def get_task_id(repository, revision, android_architecture):
    namespace = _craft_full_namespace(repository, revision, android_architecture)
    task = _index.findTask(namespace)
    return task['taskId']


def _craft_full_namespace(repository, revision, android_architecture):
    return 'gecko.v2.{repo}.nightly.revision.{revision}.mobile.{architecture}'.format(
        repo=get_minimal_repository_name(repository),
        revision=revision,
        architecture=android_architecture
    )
