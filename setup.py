from setuptools import setup, find_packages

from public_transport_watcher import project_name, version

setup(
    name=project_name,
    version=version,
    packages=find_packages(),
    install_requires=[
        "alembic >=1.15, <2.0",
        "python-dotenv>=1.0, <2.0",
        "psycopg2-binary >=2.9, <3.0",
        "sqlalchemy >=2.0, <3.0",
    ],
)
