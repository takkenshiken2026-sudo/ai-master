#!/usr/bin/env python3
"""用語マスタをシードから再構築する（rebuild_glossary へのエイリアス）。

  python3 tools/seed_glossary_terms.py
  python3 tools/seed_glossary_terms.py --sync-json  # 互換用（常に JSON 同期）
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
