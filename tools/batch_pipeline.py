"""Thin wrapper: python tools/batch_pipeline.py --batch NN [--semantic] [--no-build]
(the implementation is rag_cad.data.batch_pipeline; run with PYTHONPATH=src)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_cad.data.batch_pipeline import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
