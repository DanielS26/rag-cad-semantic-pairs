#!/usr/bin/env python3
"""Thin wrapper kept for the handoff's documented command; the checker lives in rag_cad.data.selfcheck.

Run from the repository root:  python tools/selfcheck.py --batch ... --manifest ... --report ...
Equivalent:                    python -m rag_cad.cli data selfcheck --batch ... --manifest ... --report ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag_cad.data.selfcheck import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
