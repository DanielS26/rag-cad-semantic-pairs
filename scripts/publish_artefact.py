"""Convenience wrapper around the installed project CLI."""

import sys

from rag_cad.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["artefact", "publish", *sys.argv[1:]]))