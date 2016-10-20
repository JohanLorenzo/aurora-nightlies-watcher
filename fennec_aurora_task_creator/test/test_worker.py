import aioamqp
import asyncio
import asynctest
import json
import pytest

from aioamqp.channel import Channel

from unittest.mock import Mock

from fennec_aurora_task_creator import tc_queue, publish
from fennec_aurora_task_creator.exceptions import TaskNotFoundError, TreeherderJobAlreadyExistError
from fennec_aurora_task_creator.worker import _dispatch, start_message_queue_worker


@pytest.mark.asyncio
async def test_dispatch(monkeypatch):
    body = json.dumps({
        'workerGroup': 'buildbot',
        'status': {
            'deadline': '2016-10-15T10:02:46.210Z',
            'schedulerId': '-',
            'retriesLeft': 5,
            'state': 'completed',
            'expires': '2017-10-15T10:02:46.210Z',
            'runs': [{
                'takenUntil': '2016-10-15T09:24:35.326Z',
                'workerGroup': 'buildbot',
                'reasonResolved': 'completed',
                'runId': 0,
                'reasonCreated': 'scheduled',
                'scheduled': '2016-10-15T09:02:47.598Z',
                'state': 'completed',
                'resolved': '2016-10-15T09:04:37.798Z',
                'started': '2016-10-15T09:02:48.922Z',
                'workerId': 'buildbot',
            }],
            'taskGroupId': 'QbosbKzTTB2E08IHTAtTfw',
            'provisionerId': 'null-provisioner',
            'taskId': 'QbosbKzTTB2E08IHTAtTfw',
            'workerType': 'buildbot',
        },
        'workerId': 'buildbot',
        'runId': 0,
        'version': 1,
    })

    body = body.encode(encoding='utf-8')

    monkeypatch.setattr(tc_queue, 'fetch_task_definition', lambda _: {
        'provisionerId': 'null-provisioner',
        'workerType': 'buildbot',
        'schedulerId': '-',
        'taskGroupId': 'QbosbKzTTB2E08IHTAtTfw',
        'dependencies': [],
        'requires': 'all-completed',
        'routes': [
            'index.gecko.v2.mozilla-aurora.nightly.2016.10.15.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.nightly.2016.10.15.latest.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.nightly.revision.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.nightly.latest.mobile.android-x86-opt',
            'index.buildbot.branches.mozilla-aurora.android-x86',
            'index.buildbot.revisions.7bc185ff4e8b66536bf314f9cf8b03f7d7f0b9b8.mozilla-aurora.android-x86'
        ],
        'priority': 'normal',
        'retries': 5,
        'created': '2016-10-15T09:02:46.210Z',
        'deadline': '2016-10-15T10:02:46.210Z',
        'expires': '2017-10-15T10:02:46.210Z',
        'scopes': [],
        'payload': {},
        'metadata': {
            'owner': 'mshal@mozilla.com',
            'source': 'http://hg.mozilla.org/build/mozharness/',
            'name': 'Buildbot/mozharness S3 uploader',
            'description': 'Upload outputs of buildbot/mozharness builds to S3'
        },
        'tags': {},
        'extra': {
            'index': {
                'rank': 1476471372
            }
        }
    })

    monkeypatch.setattr(publish, 'publish_if_possible', lambda _, __, ___: None)

    channel = asynctest.mock.Mock(Channel)
    envelope = Mock()
    envelope.delivery_tag = asynctest.MagicMock()

    await _dispatch(channel, body, envelope, None)
    channel.basic_client_ack.assert_called_once_with(delivery_tag=envelope.delivery_tag)

    def raise_job_already_exists(_, __, ___):
        raise TreeherderJobAlreadyExistError('', '', '')

    monkeypatch.setattr(publish, 'publish_if_possible', raise_job_already_exists)
    # JobAlreadyExistError should explictly be processed within _dispatch
    await _dispatch(channel, body, envelope, None)

    def raise_task_not_found(_, __, ___):
        raise TaskNotFoundError('', '', '')

    monkeypatch.setattr(publish, 'publish_if_possible', raise_task_not_found)
    # TaskNotFoundError should explictly be processed within _dispatch
    await _dispatch(channel, body, envelope, None)

    def raise_other_exception(_, __, ___):
        raise Exception()

    monkeypatch.setattr(publish, 'publish_if_possible', raise_other_exception)
    # Other exceptions should be caught by the general trap
    await _dispatch(channel, body, envelope, None)


@pytest.mark.asyncio
async def test_start_message_queue_worker(monkeypatch):
    config = {
        'pulse': {
            'host': 'pulse.m.o',
            'port': '5671',
            'user': 'a-user',
            'password': 'a-password',
            'queue': 'a-queue',
            'exchanges': [{
              'path': 'exchange/taskcluster-queue/v1/task-completed',
              'routing_keys': ['route.index.gecko.v2.mozilla-aurora.nightly.latest.mobile.#']
            }]
        }
    }

    channel_mock = asynctest.CoroutineMock()
    channel_mock.queue_declare = asynctest.CoroutineMock()
    channel_mock.queue_bind = asynctest.CoroutineMock()

    @asyncio.coroutine
    def mock_channel():
        return channel_mock

    protocol_mock = asynctest.Mock(asyncio.Protocol)
    protocol_mock.channel = mock_channel

    @asyncio.coroutine
    def mock_connection(host, login, password, ssl, port):
        assert host == 'pulse.m.o'
        assert port == '5671'
        assert login == 'a-user'
        assert password == 'a-password'
        assert ssl is True

        return (None, protocol_mock)

    monkeypatch.setattr(aioamqp, 'connect', mock_connection)

    await start_message_queue_worker(config)

    expected_queue_name = 'queue/a-user/a-queue'
    channel_mock.queue_declare.assert_called_once_with(queue_name=expected_queue_name, durable=True)
    channel_mock.queue_bind.assert_called_once_with(
        exchange_name='exchange/taskcluster-queue/v1/task-completed',
        queue_name=expected_queue_name,
        routing_key='route.index.gecko.v2.mozilla-aurora.nightly.latest.mobile.#'
    )

    # start_message_queue_worker() should early return
    def raise_connection_error(host, login, password, ssl, port):
        raise aioamqp.AmqpClosedConnection()

    channel_mock.queue_declare.reset_mock()
    monkeypatch.setattr(aioamqp, 'connect', raise_connection_error)
    await start_message_queue_worker(config)
    channel_mock.queue_declare.assert_not_called()
