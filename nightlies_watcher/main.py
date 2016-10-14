import asyncio
import json
import logging
import os
import taskcluster
# import uvloop

from nightlies_watcher.config import config
from nightlies_watcher.worker import worker

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
event_loop = asyncio.get_event_loop()


logger = logging.getLogger(__name__)

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')

with open(os.path.join(PROJECT_DIRECTORY, 'source_url.txt')) as f:
    source_url = f.read().rstrip()


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

# route.index.releases.v1.mozilla-beta.#:route.index.releases.v1.mozilla-esr45.#:route.index.releases.v1.mozilla-release.#


# route.index.gecko.v2.mozilla-aurora.nightly.latest.mobile.#
