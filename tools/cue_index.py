"""Thin wrapper: python tools/cue_index.py --families-dir <dir> --manifest <manifest> --output <md>
(the implementation is rag_cad.data.cue_index; run with PYTHONPATH=src)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_cad.data.cue_index import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
