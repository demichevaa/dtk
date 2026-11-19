from ..local import local_storage_impl
from ..log import FATAL
from ..storage import ObjectStorage


def make_databricks_storage(root: str) -> ObjectStorage:
    """UC volume from Databricks compute: /Volumes/... is a plain filesystem there."""
    if not root.startswith("/Volumes/"):
        FATAL("Storage(databricks_volume, %s) invalid root: must be /Volumes/<catalog>/<schema>/<volume>[/...]", root)
    return ObjectStorage("databricks_volume", root, local_storage_impl)
