"""Secure file helpers and atomic persistence utilities for Nexus Agent."""

from __future__ import annotations

import sys
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def atomic_write_text(path: Path, content: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp_file:
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    tmp_path.chmod(mode)
    tmp_path.replace(path)


def load_json_secure(path: Path, *, require_mode: int | None = None) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Secure JSON file not found: {path}")

    if require_mode is not None:
        # FIX: Skip strict chmod check on Windows (uses ACLs, not Unix modes)
        if sys.platform != "win32":
            actual_mode = path.stat().st_mode & 0o777
            if actual_mode != require_mode:
                raise PermissionError(
                    f"File {path} must be chmod {oct(require_mode)}, found {oct(actual_mode)}"
                )

    return json.loads(path.read_text(encoding="utf-8"))


def save_json_atomic(path: Path, data: Any, *, mode: int = 0o600) -> None:
    content = json.dumps(data, indent=2, sort_keys=True)
    atomic_write_text(path, content, mode=mode)
