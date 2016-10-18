import aioamqp
import logging
import json

from nightlies_watcher import tc_queue
from nightlies_watcher.exceptions import TaskNotFoundError
from nightlies_watcher.publish import publish
from nightlies_watcher.config import get_config


log = logging.getLogger(__name__)

async def worker():
    config = get_config()
    log.warn(config)

    pulse_config = config['pulse']

    try:
        transport, protocol = await aioamqp.connect(
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
    await channel.basic_qos(prefetch_count=1, prefetch_size=0,
                            connection_global=False)
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


async def _dispatch(channel, body, envelope, properties):
    body = json.loads(body.decode('utf-8'))
    log.debug('Got a new message from the queue. Channel: {}. Body: {}. Envelope: {}. Properties: {}'.format(
        channel, body, envelope, properties
    ))

    task_id = body['status']['taskId']
    config = get_config()

    try:
        task_definition = tc_queue.fetch_task_definition(task_id)
        revision = tc_queue.pluck_revision(task_definition)
        repository = tc_queue.pluck_repository(task_definition)

        log.info('Processing revision "{}" from repository "{}" (triggered by completed task "{}")'.format(
            revision, repository, task_id
        ))
        publish(config, repository, revision)

    except TaskNotFoundError as e:
        log.info('Revision "{}" does not have architecture "{}" completed yet'.format(
            revision, e.missing_android_architecture
        ))

    except Exception as e:
        log.exception('Exception {} caught by generic exception trap'.format(e))

    finally:
        log.info('Processed task "{}". Definition: {}'.format(task_id, task_definition))

        # TODO Remove that queue cleaner
        if does_route_contain_firefox(task_definition):
            log.info('Automatically acknowledging consumption of %r', task_id)
            return await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

        response = input('Should we keep it in the queue?')
        if response == 'n':
            log.info('Acknowledging consumption of %r', task_id)
            return await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        else:
            log.info('Keeping the task')


def does_route_contain_firefox(task_definition):
    matching_routes = [
        route
        for route in task_definition['routes']
        if 'firefox' in route
    ]

    return len(matching_routes) > 0
