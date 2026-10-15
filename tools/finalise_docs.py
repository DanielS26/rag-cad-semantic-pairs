"""Thin wrapper: python tools/finalise_docs.py --facts <facts.json>
(the implementation is rag_cad.data.finalise_docs; run with PYTHONPATH=src)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_cad.data.finalise_docs import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
