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
        'workerGroup': 'signing-linux-v1',
        'status': {
            'deadline': '2017-02-11T08:41:28.419Z',
            'schedulerId': 'gecko-level-3',
            'retriesLeft': 5,
            'state': 'completed',
            'expires': '2018-02-10T08:41:28.419Z',
            'runs': [{
                'runId': 0,
                'state': 'completed',
                'reasonCreated': 'scheduled',
                'reasonResolved': 'completed',
                'workerGroup': 'signing-linux-v1',
                'workerId': 'signing-linux-4',
                'takenUntil': '2017-02-10T09:54:56.358Z',
                'scheduled': '2017-02-10T09:34:52.833Z',
                'started': '2017-02-10T09:34:56.446Z',
                'resolved': '2017-02-10T09:35:29.971Z'
            }],
            'taskGroupId': 'GZItMiWuRbaAy5W4WgpwjQ',
            'provisionerId': 'scriptworker-prov-v1',
            'taskId': 'Klg1GnM4TAqeBqgz-FOdtw',
            'workerType': 'signing-linux-v1',
        },
        'workerId': 'signing-linux-4',
        'runId': 0,
        'version': 1,
    })

    body = body.encode(encoding='utf-8')

    monkeypatch.setattr(tc_queue, 'fetch_task_definition', lambda _: {
        'provisionerId': 'scriptworker-prov-v1',
        'workerType': 'signing-linux-v1',
        'schedulerId': 'gecko-level-3',
        'taskGroupId': 'GZItMiWuRbaAy5W4WgpwjQ',
        'dependencies': ['HZ-ZPFIfR7iNJhKMzB4FHw'],
        'requires': 'all-completed',
        'routes': [
            'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.latest.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.2017.02.10.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.2017.02.10.latest.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.signed-nightly.nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile.android-x86-opt',
            'index.gecko.v2.mozilla-aurora.signed-nightly.revision.6b063631a7d3ffd5dc2b621852e4d8ac8758ef99.mobile-l10n.android-x86-opt.en-US',
            'index.gecko.v2.mozilla-aurora.signed-nightly.pushdate.2017.02.10.20170210084116.mobile-l10n.android-x86-opt.en-US',
            'index.gecko.v2.mozilla-aurora.signed-nightly.latest.mobile-l10n.android-x86-opt.en-US',
        ],
        'priority': 'normal',
        'retries': 5,
        'created': '2017-02-10T08:41:28.419Z',
        'deadline': '2017-02-11T08:41:28.419Z',
        'expires': '2018-02-10T08:41:28.419Z',
        'scopes': [
            'project:releng:signing:cert:nightly-signing',
            'project:releng:signing:format:jar',
        ],
        'payload': {
            'maxRunTime': 3600,
            'upstreamArtifacts': [{
                'paths': [
                  'public/build/target.apk',
                  'public/build/en-US/target.apk',
                ],
                'formats': [
                  'jar'
                ],
                'taskId': 'HZ-ZPFIfR7iNJhKMzB4FHw',
                'taskType': 'build',
            }]
        },
        'metadata': {
            'owner': 'release@mozilla.com',
            'source': 'https://hg.mozilla.org/releases/mozilla-aurora//file/6b063631a7d3ffd5dc2b621852e4d8ac8758ef99/taskcluster/ci/build-signing',
            'description': 'Android 4.2 x86 Nightly \
([Treeherder push](https://treeherder.mozilla.org/#/jobs?repo=mozilla-aurora&revision=6b063631a7d3ffd5dc2b621852e4d8ac8758ef99)) \
Signing ([Treeherder push](https://treeherder.mozilla.org/#/jobs?repo=mozilla-aurora&revision=6b063631a7d3ffd5dc2b621852e4d8ac8758ef99))',
            'name': 'signing-android-x86-nightly/opt'
        },
        'tags': {
            'createdForUser': 'release@mozilla.com'
        },
        'extra': {
            'treeherderEnv': [
              'production',
              'staging'
            ],
            'treeherder': {
              'jobKind': 'build',
              'groupSymbol': 'tc',
              'collection': {
                'opt': True
              },
              'machine': {
                'platform': 'android-4-2-x86'
              },
              'groupName': 'Executed by TaskCluster',
              'tier': 1,
              'symbol': 'Ns'
             }
        }
    })

    monkeypatch.setattr(publish, 'publish_if_possible', lambda _, __, ___: None)

    channel = asynctest.mock.Mock(Channel)
    envelope = Mock()
    envelope.delivery_tag = asynctest.MagicMock()

    await _dispatch(channel, body, envelope, None)
    channel.basic_client_ack.assert_called_once_with(delivery_tag=envelope.delivery_tag)
    channel.basic_client_ack.reset_mock()

    def raise_job_already_exists(_, __, ___):
        raise TreeherderJobAlreadyExistError('', '', '')

    monkeypatch.setattr(publish, 'publish_if_possible', raise_job_already_exists)
    # JobAlreadyExistError should explictly be processed within _dispatch
    await _dispatch(channel, body, envelope, None)
    channel.basic_client_ack.assert_called_once_with(delivery_tag=envelope.delivery_tag)
    channel.basic_client_ack.reset_mock()

    def raise_task_not_found(_, __, ___):
        raise TaskNotFoundError('', '', '')

    monkeypatch.setattr(publish, 'publish_if_possible', raise_task_not_found)
    # TaskNotFoundError should explictly be processed within _dispatch
    await _dispatch(channel, body, envelope, None)
    channel.basic_client_ack.assert_called_once_with(delivery_tag=envelope.delivery_tag)
    channel.basic_client_ack.reset_mock()

    def raise_other_exception(_, __, ___):
        raise Exception()

    monkeypatch.setattr(publish, 'publish_if_possible', raise_other_exception)
    # Other exceptions should be caught by the general trap, but shouldn't mark the message as read
    await _dispatch(channel, body, envelope, None)
    channel.basic_client_ack.assert_not_called()


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
