import asyncio
import logging
import taskcluster

from fennec_aurora_task_creator.config import get_config
from fennec_aurora_task_creator.worker import start_message_queue_worker

logger = logging.getLogger(__name__)


def main(name=None):
    if name not in ('__main__', None):
        return

    config = get_config()

    FORMAT = '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    level = logging.DEBUG if config.get('verbose', False) else logging.INFO
    logging.basicConfig(format=FORMAT, level=level)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('taskcluster').setLevel(logging.WARNING)
    logging.getLogger('mohawk').setLevel(logging.WARNING)

    taskcluster.config['credentials']['clientId'] = config['credentials']['client_id']
    taskcluster.config['credentials']['accessToken'] = config['credentials']['access_token']

    event_loop = asyncio.get_event_loop()

    try:
        event_loop.run_until_complete(start_message_queue_worker(config))
        event_loop.run_forever()
    except KeyboardInterrupt:
        # TODO: make better shutdown
        logger.exception('KeyboardInterrupt registered, exiting.')
        event_loop.stop()
        while event_loop.is_running():
            pass
        event_loop.close()
        exit()


main(__name__)
