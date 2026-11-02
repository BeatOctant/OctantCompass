"""Absolute imports for the standalone entry point."""

import multiprocessing

from octantcompass.cli import main

if __name__ == "__main__":
    # The executable is also the child process that builds a new DB folder (engine/octantvector.py).
    multiprocessing.freeze_support()
    # A spawned child would otherwise run this file again from the path it has here. Children of the window get
    # PYINSTALLER_RESET_ENVIRONMENT (frozen.py) and unpack themselves elsewhere, where that path does not exist. The
    # child needs nothing from this file: what it runs is imported from octantcompass.
    del globals()["__file__"]
    raise SystemExit(main())
