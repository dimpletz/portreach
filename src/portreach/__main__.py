"""Entry point for running portreach as a module: python -m portreach"""

import sys

from portreach.cli import main

if __name__ == "__main__":
    sys.exit(main())
