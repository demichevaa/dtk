import os
import platform
import socket
import shlex
import sys
from pathlib import Path

RUNTIME_ENV_DEFAULT = (
    "PYTHONPATH",
    "PYTHONHOME",
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "PYSPARK_PYTHON",
    "SPARK_HOME",
    "JAVA_HOME",
    "DATABRICKS_RUNTIME_VERSION",
    "DATABRICKS_CONFIG_PROFILE",
    "TZ",
    "LANG",
)


def _env() -> dict:
    extra = [n.strip() for n in os.environ.get("SDK_RUNTIME_ENV", "").split(",") if n.strip()]
    names = set(RUNTIME_ENV_DEFAULT) | set(extra)
    return {k: v for k, v in sorted(os.environ.items()) if k.startswith("SDK_") or k in names}


def RUNTIME() -> dict:
    script = sys.argv[0] if sys.argv and sys.argv[0] not in ("", "-c") else None
    return {
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "workdir": str(Path.cwd()),
        "command": shlex.join(getattr(sys, "orig_argv", sys.argv)),
        "script": str(Path(script).resolve()) if script else None,
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "venv": sys.prefix if sys.prefix != sys.base_prefix else None,
        "base_prefix": sys.base_prefix,
        "pythonpath": [str(Path(p).resolve()) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p],
        "os": platform.platform(),
        "env": _env(),
    }
