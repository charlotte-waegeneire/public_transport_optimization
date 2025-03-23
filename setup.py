from setuptools import setup, find_packages

from public_transport_watcher import project_name, version

setup(
    name=project_name,
    version=version,
    packages=find_packages(),
    install_requires=[],
)