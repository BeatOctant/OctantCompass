"""A stand-in for octantvector.runtime that a spawned child imports (test_octantvector.py
test_updates_run_in_a_child_process): only what apply_update and import_archive need."""
import os
import warnings
from pathlib import Path


class DBError(Exception):
    pass


class VersionError(DBError):
    pass


class SignatureWarning(UserWarning):
    pass


def apply_update(files, base, out, trust=None):
    Path(out).mkdir()
    (Path(out) / "pid").write_text(str(os.getpid()))
    warnings.warn(SignatureWarning(f"{Path(out).name}: synthetic: no manifest.sig"))
    return Path(out)


def import_archive(path, out, trust=None):
    if Path(path).name.startswith("newer"):
        raise VersionError("schemaVersion '3.0' (this OctantVector reads 2.x)")
    raise DBError("broken archive")


class _DB:
    def __init__(self, path):
        self.path = Path(path)

    def info(self):
        return {"dbVersion": self.path.name, "pid": os.getpid()}


def open_db(path):
    if Path(path).name.startswith("newer"):
        raise VersionError("schemaVersion '3.0' (this OctantVector reads 2.x)")
    return _DB(path)
