from taskcluster import Index

_index = Index()


def get_latest_task_id(repository, android_architecture):
    namespace = _get_full_name_space(repository, android_architecture)
    task = _index.findTask(namespace)
    return task['taskId']


def _get_full_name_space(repository, android_architecture):
    return 'gecko.v2.{}.nightly.latest.mobile.{}'.format(_get_minimal_repository_name(repository), android_architecture)


def _get_minimal_repository_name(repository):
    return repository.split('/')[-1]
