import os
from typing import Optional

from .log import FATAL


def _default_backend() -> str:
    if os.environ.get("SDK_SPARK_BACKEND"):
        return os.environ["SDK_SPARK_BACKEND"]
    return "databricks" if "DATABRICKS_RUNTIME_VERSION" in os.environ else "local"


def new_spark(backend: Optional[str] = None, conf: Optional[dict] = None):
    backend = backend or _default_backend()
    from pyspark.sql import SparkSession

    if backend == "databricks":
        return SparkSession.builder.getOrCreate()

    if backend == "local":
        builder = SparkSession.builder.master("local[*]").appName("sdk")
        for k, v in (conf or {}).items():
            builder = builder.config(k, v)
        return builder.getOrCreate()

    FATAL("Spark(%s) unknown backend: expected 'databricks' or 'local'", backend)


_global = None
_global_backend: Optional[str] = None


def SPARK_INIT(backend: str, conf: Optional[dict] = None):
    global _global, _global_backend
    if _global is not None and _global_backend != backend:
        FATAL("Spark(%s) already in use, can't switch to %s", _global_backend, backend)
    if _global is None:
        _global, _global_backend = new_spark(backend, conf), backend
    return _global


class _GlobalSpark:
    def __getattr__(self, name):
        global _global, _global_backend
        if _global is None:
            _global_backend = _default_backend()
            _global = new_spark(_global_backend)
        return getattr(_global, name)


SPARK = _GlobalSpark()
