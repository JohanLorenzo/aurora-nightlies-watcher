import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'version.txt')) as f:
    version = f.read().rstrip()

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'source_url.txt')) as f:
    source_url = f.read().rstrip()

setup(
    name="nightlies-watcher",
    version=version,
    description="Watches Aurora nightlies and creates tasks to deploy them to Google Play Store",
    author="Mozilla Release Engineering",
    author_email="release+python@mozilla.com",
    url=source_url,
    packages=find_packages(),
    package_data={"nightlies-watcher": ["data/*"]},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "nightlies-watcher = nightlies_watcher.watch:main",
        ],
    },
    license="MPL2",
    install_requires=[
        "aioamqp==0.8.2",
        "frozendict==1.2",
        "treeherder-client==3.1.0",
        "requests==2.11.1",
        "taskcluster==0.3.4",
    ],
)
