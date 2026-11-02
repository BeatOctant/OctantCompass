"""Contract-1 adapter. Only this module may import OctantVector.

apply_update, import_archive and check_db run in a child process: building or opening a DB folder holds a whole DB's
tables and vectors for a while, and a host or window that did it itself would keep much of that memory after it is
done. The child's memory goes back to the OS when it ends."""

import multiprocessing
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..frozen import restore_import_path
from . import (DBError, EngineIncompatibleError, EngineUnavailableError, RequestError, SeedNotEmbeddedError,
               SeedNotInDBError, SignatureWarning, UnknownPresetError, VersionError, recorded)


# The contract-1 runtime API this OctantCompass uses: the same major version, and at least this minor
# version (OctantSpecs contracts/engine-runtime.md, 版の付け方). Presets, expand_preset, SeedNotEmbeddedError and
# UnknownPresetError joined 1.0 without a new version, and so did import_archive and info()'s notice and credits;
# the OctantVector this OctantCompass installs (0.9) has them all, read_info too, and the 0.8.0 guards against a tar bomb
# and runaway params.
SUPPORTED_API = (1, 0)


def is_supported(api_version):
    try:
        major, minor = (int(part) for part in api_version.split("."))
    except (AttributeError, TypeError, ValueError):
        return False
    return major == SUPPORTED_API[0] and minor >= SUPPORTED_API[1]


def _check_db(runtime, path):
    """Open the DB as the host will, and keep only what it says (its info)."""
    return runtime.open_db(path).info()


def _in_child(module, name, args):
    """Run in the child process: OctantVector's `name`(*args) -> ("ok", result, signature warnings) or
    ("VersionError" | "DBError", message, signature warnings). Other errors reach the parent as they are."""
    import importlib
    restore_import_path()
    runtime = importlib.import_module(module)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", runtime.SignatureWarning)
        try:
            function = (lambda *a: _check_db(runtime, *a)) if name == "check_db" else getattr(runtime, name)
            outcome = ("ok", function(*args))
        except runtime.VersionError as exc:
            outcome = ("VersionError", str(exc))
        except runtime.DBError as exc:
            outcome = ("DBError", str(exc))
    for warning in caught:
        if not issubclass(warning.category, runtime.SignatureWarning):
            warnings.showwarning(warning.message, warning.category, warning.filename, warning.lineno)
    return (*outcome, [str(w.message) for w in caught if issubclass(w.category, runtime.SignatureWarning)])


class OctantVectorEngine:
    # The module the child process imports for apply_update and import_archive; None runs them in this process.
    child_runtime = "octantvector.runtime"

    def __init__(self):
        self._runtime = None

    def _load_runtime(self):
        if self._runtime is not None:
            return self._runtime
        try:
            import octantvector.runtime as runtime
        except ImportError as exc:
            raise EngineUnavailableError("OctantVector runtime is unavailable") from exc
        if not is_supported(getattr(runtime, "API_VERSION", None)):
            raise EngineIncompatibleError("OctantVector runtime API is outside the supported range")
        self._runtime = runtime
        return runtime

    def _call(self, function, *args):
        runtime = self._load_runtime()
        try:
            return function(*args)
        except runtime.VersionError as exc:
            raise VersionError(str(exc)) from exc
        except runtime.DBError as exc:
            raise DBError(str(exc)) from exc
        except runtime.SeedNotEmbeddedError as exc:
            raise SeedNotEmbeddedError(str(exc)) from exc
        except runtime.SeedNotInDBError as exc:
            raise SeedNotInDBError(str(exc)) from exc
        except runtime.UnknownPresetError as exc:
            raise UnknownPresetError(str(exc)) from exc
        except runtime.RequestError as exc:
            raise RequestError(str(exc)) from exc

    def open_db(self, path):
        runtime = self._load_runtime()
        if not Path(path).exists():
            raise FileNotFoundError(path)
        return self._call(runtime.open_db, path)

    def db_info(self, db):
        return self._call(db.info)

    def read_info(self, path):
        runtime = self._load_runtime()
        if not Path(path).exists():
            raise FileNotFoundError(path)
        return self._call(runtime.read_info, path)

    def recommend(self, db, history, request, params):
        runtime = self._load_runtime()
        return self._call(runtime.recommend, db, history, request, params)

    def presets(self, db):
        runtime = self._load_runtime()
        return self._call(runtime.presets, db)

    def expand_preset(self, db, request):
        runtime = self._load_runtime()
        return self._call(runtime.expand_preset, db, request)

    def describe(self, db, history, params):
        runtime = self._load_runtime()
        return self._call(runtime.describe, db, history, params)

    def plan_update(self, index, local_version):
        runtime = self._load_runtime()
        return self._call(runtime.plan_update, index, local_version)

    def apply_update(self, files, base, out, trust=None):
        return self._signed("apply_update", files, base, out, trust)

    def import_archive(self, path, out, trust=None):
        return self._signed("import_archive", path, out, trust)

    def check_db(self, path):
        runtime = self._load_runtime()
        if not Path(path).exists():
            raise FileNotFoundError(path)
        if self.child_runtime is None:
            return self._call(_check_db, runtime, path)
        return self._signed("check_db", path)

    def _signed(self, name, *args):
        runtime = self._load_runtime()
        # OctantVector's SignatureWarning goes on as OctantCompass's own, as the errors do.
        if self.child_runtime is None:
            with recorded(runtime.SignatureWarning) as signatures:
                result = self._call(getattr(runtime, name), *args)
        else:
            with ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("spawn")) as child:
                kind, result, signatures = child.submit(_in_child, self.child_runtime, name, args).result()
            if kind == "VersionError":
                raise VersionError(result)
            if kind == "DBError":
                raise DBError(result)
        for text in signatures:
            warnings.warn(SignatureWarning(text), stacklevel=3)
        return result
