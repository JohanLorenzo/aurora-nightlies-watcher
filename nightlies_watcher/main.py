import asyncio
import logging
import taskcluster

from nightlies_watcher.config import get_config
from nightlies_watcher.worker import start_message_queue_worker

logger = logging.getLogger(__name__)


def main(name=None):
    if name not in ('__main__', None):
        return

    FORMAT = '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    # logging.getLogger('taskcluster').setLevel(logging.WARNING)

    config = get_config()

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
