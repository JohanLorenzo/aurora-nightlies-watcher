import aioamqp
import logging
import json

from fennec_aurora_task_creator import tc_queue, publish
from fennec_aurora_task_creator.exceptions import TaskNotFoundError, TreeherderJobAlreadyExistError
from fennec_aurora_task_creator.config import get_config


log = logging.getLogger(__name__)


async def start_message_queue_worker(config):
    pulse_config = config['pulse']

    try:
        _, protocol = await aioamqp.connect(
            host=pulse_config['host'],
            login=pulse_config['user'],
            password=pulse_config['password'],
            ssl=True,
            port=pulse_config['port'],
        )
    except aioamqp.AmqpClosedConnection as acc:
        log.exception('AMQP Connection closed: %s', acc)
        return

    channel = await protocol.channel()
    await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)

    queue_name = 'queue/{}/{}'.format(pulse_config['user'], pulse_config['queue'])
    log.info('Using queue: %s', queue_name)

    await channel.queue_declare(queue_name=queue_name, durable=True)
    for exchange in pulse_config['exchanges']:
        for key in exchange['routing_keys']:
            log.info("Binding %s using %s", exchange, key)
            await channel.queue_bind(exchange_name=exchange['path'],
                                     queue_name=queue_name,
                                     routing_key=key)
    await channel.basic_consume(_dispatch, queue_name=queue_name)

    log.info('Worker has completed running.')


async def _dispatch(channel, body, envelope, _):
    body = json.loads(body.decode('utf-8'))
    log.debug('Got a new message from the queue. Body: {}'.format(body))

    task_id = body['status']['taskId']
    config = get_config()

    try:
        route_pattern = config['taskcluster_index_pattern']
        task_definition = tc_queue.fetch_task_definition(task_id)
        revision = tc_queue.pluck_revision(route_pattern, task_definition)
        repository = tc_queue.pluck_repository(route_pattern, task_definition)

        log.info('Processing revision "{}" from repository "{}" (triggered by completed task "{}")'.format(
            revision, repository, task_id
        ))
        publish.publish_if_possible(config, repository, revision)

    except TreeherderJobAlreadyExistError:
        log.warn('A treeherder job already exists for revision "{}" in repository "{}"'.format(revision, repository))

    except TaskNotFoundError as e:
        log.info('Revision "{}" does not have architecture "{}" completed yet'.format(
            revision, e.missing_android_architecture
        ))

    except Exception as e:
        log.exception('Exception "{}" caught by generic exception trap'.format(e))

    finally:
        log.info('Marking message as read. Processed task "{}"'.format(task_id))
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
