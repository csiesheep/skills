"""管線入口：py -X utf8 pipe.py <index|fetch|corpus|annotate|stats|generate|...>

等於在 scripts/ 底下跑 py -m storypipe.cli；從任何工作資料夾都能叫。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from storypipe.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
