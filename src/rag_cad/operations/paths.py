"""Fail-closed guards for active local computation, not artefact storage roots."""

import os
from pathlib import Path, PureWindowsPath

DRIVE_NAMES = {"drive", "mydrive", "shareddrives", "shared drives"}


def local_path(path: Path, workspace: Path | None = None) -> Path:
    text = str(path)
    windows = PureWindowsPath(text)
    if text.startswith(("//", "\\\\")) or (os.name != "nt" and windows.drive):
        raise ValueError("Network/foreign absolute paths are forbidden for active work")
    if any(part.casefold() in DRIVE_NAMES for part in text.replace("\\", "/").split("/")):
        raise ValueError("Active paths must not point into Drive")
    absolute = path.absolute()
    for item in (absolute, *absolute.parents):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("Linked active paths are forbidden")
    resolved = absolute.resolve()
    if any(part.casefold() in DRIVE_NAMES for part in resolved.parts):
        raise ValueError("Resolved active path points into Drive")
    if workspace is not None and not resolved.is_relative_to(local_path(workspace)):
        raise ValueError("Active inputs and outputs must stay inside the workspace")
    return resolved


def execution_paths(args) -> None:
    workspace = local_path(args.workspace)
    for name in ("source", "resources", "model_bundle", "output", "destination", "receipt"):
        value = getattr(args, name, None)
        if value is not None:
            local_path(value, workspace)
    output = getattr(args, "output", None)
    if output is not None:
        for name in ("source", "resources", "model_bundle", "destination"):
            value = getattr(args, name, None)
            if value is not None:
                source = Path(value).resolve()
                target = Path(output).resolve()
                if target.is_relative_to(source) or source.is_relative_to(target):
                    raise ValueError("Active output must not overlap its input directories")