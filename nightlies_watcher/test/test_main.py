import asyncio
import pytest

from unittest import mock

from nightlies_watcher.main import main


def test_main():
    loop = mock.MagicMock()
    loop.run_until_complete = lambda _: None
    loop.run_forever = lambda: None

    with mock.patch.object(asyncio, 'get_event_loop') as get_event_loop:
        get_event_loop.return_value = loop
        main()


def test_main_stops_on_ctrl_c():
    loop = mock.MagicMock()

    def raise_keyboard_interrupt():
        raise KeyboardInterrupt

    loop.run_until_complete = lambda _: None
    loop.run_forever = raise_keyboard_interrupt

    loop.is_running = mock.MagicMock()
    # Make is_running() not skip the while loop
    loop.is_running.side_effect = lambda: loop.is_running.call_count < 2

    with mock.patch.object(asyncio, 'get_event_loop') as get_event_loop:
        get_event_loop.return_value = loop

        with pytest.raises(SystemExit):
            main()
