import pytest

from nightlies_watcher.exceptions import NoTreeherderResultSetError, TooManyTreeherderResultSetsError
from nightlies_watcher.treeherder import _is_job_in_list, _client, does_job_already_exist, get_routes


def test_is_job_in_list():
    jobs = [{'job_type_name': 'Google Play Publisher'}, {'job_type_name': 'Build'}]
    assert _is_job_in_list(jobs, 'Google Play Publisher')

    jobs = [{'job_type_name': 'Build'}]
    assert not(_is_job_in_list(jobs, 'Google Play Publisher'))


def test_does_job_already_exist(monkeypatch):
    monkeypatch.setattr(_client, 'get_resultsets', lambda project, revision: [{'id': 13769}])
    monkeypatch.setattr(_client, 'get_jobs', lambda repository, count, result_set_id, tier: [
        {'job_type_name': 'Google Play Publisher'}, {'job_type_name': 'Build'}
    ])
    assert does_job_already_exist(
        'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'Google Play Publisher', tier=3
    )

    monkeypatch.setattr(_client, 'get_jobs', lambda repository, count, result_set_id, tier: [
        {'job_type_name': 'Build'}
    ])
    assert not(does_job_already_exist(
        'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'Google Play Publisher', tier=3
    ))


def test_does_job_already_exist_fails_if_no_resulset_is_found(monkeypatch):
    monkeypatch.setattr(_client, 'get_resultsets', lambda project, revision: [])
    with pytest.raises(NoTreeherderResultSetError):
        does_job_already_exist(
            'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'Google Play Publisher', tier=3
        )


def test_does_job_already_exist_fails_if_too_many_results_are_found(monkeypatch):
    monkeypatch.setattr(_client, 'get_resultsets', lambda project, revision: [{'id': 13769}, {'id': 999999}])
    with pytest.raises(TooManyTreeherderResultSetsError):
        does_job_already_exist(
            'mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'Google Play Publisher', tier=3
        )


def test_get_routes():
    assert get_routes('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', '10148') == [
        'tc-treeherder.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
        'tc-treeherder-stage.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
    ]
