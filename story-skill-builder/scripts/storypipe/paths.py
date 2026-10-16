"""管線找檔案的地方。

資料（data/）放在目前工作目錄，也就是某個類型的工作資料夾，不進 repo。
類型設定（prompts/ 等）預設是這個 skill 附的範例類型 ghost-story；
要做別的類型，把環境變數 STORYPIPE_GENRE 指到那個類型的資料夾。
"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
GENRE_DIR = Path(os.environ.get("STORYPIPE_GENRE") or SKILL_DIR / "genres" / "ghost-story")
PROMPTS_DIR = GENRE_DIR / "prompts"
