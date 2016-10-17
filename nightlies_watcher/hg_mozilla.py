import requests

from nightlies_watcher.exceptions import NoPushIdError, TooManyPushIdsError


def get_minimal_repository_name(repository):
    return repository.split('/')[-1]


def get_push_id(repository, revision):
    response = requests.get(_get_push_log_url(repository, revision), timeout=10)
    return _pluck_push_id(response.json(), revision)


def _get_push_log_url(repository, revision):
    return 'https://hg.mozilla.org/{}/json-pushes?changeset={}'.format(repository, revision)


def _pluck_push_id(push_log_json, revision):
    push_log_ids = tuple(push_log_json.keys())

    if len(push_log_ids) == 0:
        raise NoPushIdError(revision)
    elif len(push_log_ids) != 1:
        raise TooManyPushIdsError(revision)

    return push_log_ids[0]
