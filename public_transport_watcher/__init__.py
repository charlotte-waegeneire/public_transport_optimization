import os

project_name = "public_transport_watcher"
version = open(os.path.join(os.path.dirname(__file__), "VERSION.txt")).read().strip()

__all__ = ["project_name", "version"]
