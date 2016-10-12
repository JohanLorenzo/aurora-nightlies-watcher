from taskcluster import Index
from nightlies_watcher.hg_mozilla import get_minimal_repository_name

_index = Index()


def get_latest_task_id(repository, android_architecture):
    namespace = _get_full_name_space(repository, android_architecture)
    task = _index.findTask(namespace)
    return task['taskId']


def _get_full_name_space(repository, android_architecture):
    return 'gecko.v2.{}.nightly.latest.mobile.{}'.format(get_minimal_repository_name(repository), android_architecture)
