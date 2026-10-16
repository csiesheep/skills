"""故事產生器管線：抓取、標註、統計、規劃、寫作、評審。"""
import sys as _sys

# Windows 主控台重導向時預設 cp1252，印中文會炸；統一成 UTF-8。
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
