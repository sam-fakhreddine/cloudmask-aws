"""Allow running cloudmask.cli as a module: python -m cloudmask.cli."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
