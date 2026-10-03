"""exe にするときの入口（PyInstaller 用）。ふだんは python -m webcollect で動かす。"""

import sys

from webcollect.cli import main

if __name__ == "__main__":
    sys.exit(main())
