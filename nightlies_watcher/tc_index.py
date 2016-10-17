from taskcluster import Index
from nightlies_watcher.hg_mozilla import get_minimal_repository_name

_index = Index()


def get_task_id(repository, revision, android_architecture):
    namespace = craft_full_namespace(repository, android_architecture)
    task = _index.findTask(namespace)
    return task['taskId']


def craft_full_namespace(repository, android_architecture, revision='latest'):
    revision = revision if revision == 'latest' else 'revision.{}'.format(revision)

    return 'gecko.v2.{repo}.nightly.{revision_or_latest}.mobile.{architecture}'.format(
        repo=get_minimal_repository_name(repository),
        revision_or_latest=revision,
        architecture=android_architecture
    )
