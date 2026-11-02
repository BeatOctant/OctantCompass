"""What differs when OctantCompass runs as a PyInstaller executable."""

import os
import sys


# The import path this process started with. A child that multiprocessing spawns is handed its parent's sys.path; a
# child of the window unpacks itself elsewhere (system_environment), so that path names the parent's files, not its own.
STARTUP_PATH = tuple(sys.path)


def restore_import_path():
    """In a spawned child of the executable, import from its own unpacked files again (STARTUP_PATH)."""
    if getattr(sys, "frozen", False):
        sys.path[:] = STARTUP_PATH


def system_environment():
    """The environment for programs this one starts. A PyInstaller executable points LD_LIBRARY_PATH at its own
    bundled libraries, and GI_TYPELIB_PATH at its typelibs (the window on Linux), which can break the programs
    WebKitGTK runs, a browser or another copy of OctantCompass; give them back the original values.

    Another copy of OctantCompass (the window starting the host, the host opening the window) is told to unpack itself
    again: by default the one-file executable reuses this one's unpacked files, which are removed when this one ends,
    so a host started from the window would lose its files when the window closes."""
    environment = dict(os.environ)
    if getattr(sys, "frozen", False):
        original = environment.pop("LD_LIBRARY_PATH_ORIG", None)
        if original is None:
            environment.pop("LD_LIBRARY_PATH", None)
        else:
            environment["LD_LIBRARY_PATH"] = original
        if environment.get("GI_TYPELIB_PATH", "").startswith(sys._MEIPASS):
            environment.pop("GI_TYPELIB_PATH")
        environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return environment


def use_system_environment():
    """From now on, programs started by libraries in this process (WebKitGTK's own, a browser for a link) get the
    system environment. This process keeps finding its libraries and typelibs: both were read when it started and
    when PyGObject first loaded."""
    environment = system_environment()
    os.environ.clear()
    os.environ.update(environment)
