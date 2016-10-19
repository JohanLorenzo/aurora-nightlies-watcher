# nightlies-watcher

[![Build Status](https://travis-ci.org/JohanLorenzo/nightlies-watcher.svg?branch=master)](https://travis-ci.org/JohanLorenzo/nightlies-watcher) [![Coverage Status](https://coveralls.io/repos/github/JohanLorenzo/nightlies-watcher/badge.svg?branch=master)](https://coveralls.io/github/JohanLorenzo/nightlies-watcher?branch=master)

Create publishing tasks once Firefox for Android nightlies are built. It currently only supports publishing to Google Play Store.


## Get the code

First, you need `python>=3.5.0`.

``` shell
# create the virtualenv in ./venv3
virtualenv3 venv3
# activate it
. venv3/bin/activate
pip install nightlies-watcher
```

## Configure

``` shell
    cp config_example.json config.json
    # edit it with your favorite text editor
```

There are many values to edit. Example values and details below should give you a hint about what to provide. If not, please contact the author for other unclear areas.

### Taskcluster credentials

Task will be created so that an instance of [pushapkscriptworker](https://github.com/mozilla-releng/pushapkworker) picks it up. Deploying to the current Mozilla's instance requires these scopes for your taskcluster client.
```
project:releng:googleplay:aurora
queue:create-task:scriptworker-prov-v1/pushapk-v1
queue:route:tc-treeherder-stage.v2.mozilla-aurora.*
queue:route:tc-treeherder.v2.mozilla-aurora.*
```

Here you may [create and edit scopes](https://tools.taskcluster.net/auth/clients).

### Pulse config

In order to know when builds are ready, nightlies-watcher relies on [Pulse](https://wiki.mozilla.org/Auto-tools/Projects/Pulse). Here you may [create a client](https://pulseguardian.mozilla.org/profile). If you're using Mozilla's instance, you'll need to listen to the [task completed exchange](https://wiki.mozilla.org/Auto-tools/Projects/Pulse/Exchanges#Queue:_Task_Completed), which translates to:
```
exchange/taskcluster-queue/v1/task-completed
```
At the first start of nightlies-watcher, a pulse queue will be created. If you're still using Mozilla's instance, nightlies are found under these keys:
```
route.index.gecko.v2.$BRANCH.nightly.latest.$PLATFORM.#
```
You may find the values of `$BRANCH` and `$PLATFORM` by [exploring the Taskcluster index](https://tools.taskcluster.net/index/artifacts/#gecko.v2/gecko.v2).

### Architectures to watch

Configuration follows this pattern:
```json
{
  "architecture defined in pushapkworker": "equivalent architecture defined in taskcluster"
}
```
