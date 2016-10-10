import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'version.txt')) as f:
    version = f.read().rstrip()

setup(
    name="nightlies-watcher",
    version=version,
    description="Watches Aurora nightlies and creates tasks to deploy them to Google Play Store",
    author="Mozilla Release Engineering",
    author_email="release+python@mozilla.com",
    url="https://github.com/mozilla-releng/nightlies-watcher",
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
        "taskcluster==0.3.4",
    ],
)
