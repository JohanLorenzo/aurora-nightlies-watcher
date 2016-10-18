from nightlies_watcher.tc_index import get_task_id, _craft_full_namespace, _index


def test_craft_full_namespace():
    assert _craft_full_namespace('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'android-api-15') == \
        'gecko.v2.mozilla-aurora.nightly.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-api-15'


def test_get_task_id(monkeypatch):
    monkeypatch.setattr(_index, 'findTask', lambda _: {'taskId': 'VRzn3vi6RvSNaKTaT5u83A'})
    assert get_task_id('mozilla-aurora', '7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8', 'android-api-15') == \
        'VRzn3vi6RvSNaKTaT5u83A'
