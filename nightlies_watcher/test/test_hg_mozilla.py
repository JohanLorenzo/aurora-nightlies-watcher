import pytest

from nightlies_watcher.hg_mozilla import get_minimal_repository_name, get_push_id, _get_push_log_url, _pluck_push_id
from nightlies_watcher.exceptions import NoPushIdError, TooManyPushIdsError


def test_get_minimal_repository_name():
    assert get_minimal_repository_name('releases/mozilla-aurora') == 'mozilla-aurora'


def test_get_push_log_url():
    assert _get_push_log_url('releases/mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8') == \
        'https://hg.mozilla.org/releases/mozilla-aurora/json-pushes?changeset=7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8'

PUSH_LOG_JSON = {
    '10148': {
        'changesets': [
            '88e2a41ad412fcce8da9c46777ac9ec01dcc450d',
            '24f9300535ef2054c3a367d6769e519ba836c8ed',
            '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8'
        ],
        'date': 1476471372,
        'user': 'ryanvm@gmail.com'
    }
}


def test_pluck_push_id():
    assert _pluck_push_id(PUSH_LOG_JSON, '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8') == '10148'

    with pytest.raises(NoPushIdError):
        _pluck_push_id({}, '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8')

    with pytest.raises(TooManyPushIdsError):
        _pluck_push_id({
            '10148': {},
            '10149': {},
        }, '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8')


def test_get_push_id(monkeypatch):
    def requests_patch(_, timeout):
        class DummyReponse():
            def json(_):
                return PUSH_LOG_JSON

        return DummyReponse()

    import requests
    monkeypatch.setattr(requests, 'get', requests_patch)

    assert get_push_id('releases/mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8') == '10148'
