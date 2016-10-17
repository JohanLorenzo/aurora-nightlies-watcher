from nightlies_watcher.treeherder import get_routes


def test_get_routes():
    assert get_routes('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', '10148') == \
        [
            'tc-treeherder.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
            'tc-treeherder-stage.v2.mozilla-aurora.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.10148',
        ]
