from .cli import main

if __name__ == "__main__":  # not when a child process imports it (engine/octantvector.py)
    raise SystemExit(main())
