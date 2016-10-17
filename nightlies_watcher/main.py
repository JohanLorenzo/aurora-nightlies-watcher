import asyncio
import logging
import os
import taskcluster

from nightlies_watcher.config import config
from nightlies_watcher.worker import worker

event_loop = asyncio.get_event_loop()


logger = logging.getLogger(__name__)

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')


def main(name):
    if name not in ('__main__', None):
        return

    FORMAT = '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    # logging.getLogger('taskcluster').setLevel(logging.WARNING)

    taskcluster.config['credentials']['clientId'] = config['credentials']['client_id']
    taskcluster.config['credentials']['accessToken'] = config['credentials']['access_token']

    try:
        event_loop.run_until_complete(worker())
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
