from setuptools import find_packages, setup

from public_transport_watcher import project_name, version

setup(
    name=project_name,
    version=version,
    packages=find_packages(),
    install_requires=[
        "alembic >=1.15, <2.0",
        "beautifulsoup4 >=4.12, <5.0",
        "flask >=3.0.0, <4.0",
        "matplotlib >=3.10, <4.0",
        "networkx >=3.4.2, <4.0",
        "pandas >=2.2.3, <3.0",
        "psycopg2-binary >=2.9, <3.0",
        "python-dotenv>=1.0, <2.0",
        "requests >=2.31, <3.0",
        "schedule >=1.2, <2.0",
        "sqlalchemy >=2.0, <3.0",
        "streamlit >=1.45.1, <2.0",
    ],
)
