from nightlies_watcher.hg_mozilla import get_minimal_repository_name


def test_get_minimal_repository_name():
    assert get_minimal_repository_name('releases/mozilla-aurora') == 'mozilla-aurora'
