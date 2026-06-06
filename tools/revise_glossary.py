#!/usr/bin/env python3
"""用語の追加・削除後にマスタを再構築する（rebuild_glossary へのエイリアス）。

  語の追加: tools/glossary_seed/<カテゴリ>.py の TERMS に追記
  語の削除: tools/glossary_seed/removals.py の REMOVAL_IDS に追加
  再構築:   python3 tools/rebuild_glossary.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cmd = [sys.executable, str(ROOT / "tools" / "rebuild_glossary.py")]
    if "--dry-run" in sys.argv:
        cmd.append("--dry-run")
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
