from __future__ import annotations

import os
import shutil
import time
from typing import Iterable, List, Optional

class RollbackPoint:
    def __init__(self, *, created_at: float, root: str, files: List[str]) -> None:
        self.created_at = float(created_at)
        self.root = str(root)
        self.files = list(files)


class SafeRollbackSystem:
    """Minimal rollback system for sandboxed code edits.

    This is intentionally file-based and scoped to a sandbox root.
    """

    def __init__(self, *, sandbox_root: str, backup_dir: Optional[str] = None) -> None:
        self.sandbox_root = os.path.abspath(sandbox_root)
        self.backup_dir = os.path.abspath(backup_dir or os.path.join(self.sandbox_root, ".rollback"))
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_point(self, rel_paths: Iterable[str]) -> RollbackPoint:
        ts = time.time()
        tag = time.strftime("%Y%m%d_%H%M%S")
        rp_root = os.path.join(self.backup_dir, f"rp_{tag}_{int(ts * 1000)}")
        os.makedirs(rp_root, exist_ok=True)

        files: List[str] = []
        for rel in rel_paths:
            rel = rel.replace("\\", "/").lstrip("/")
            src = os.path.join(self.sandbox_root, rel)
            if not os.path.exists(src):
                continue
            dst = os.path.join(rp_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            files.append(rel)

        return RollbackPoint(created_at=ts, root=rp_root, files=files)

    def restore(self, point: RollbackPoint) -> bool:
        try:
            for rel in point.files:
                src = os.path.join(point.root, rel)
                dst = os.path.join(self.sandbox_root, rel)
                if not os.path.exists(src):
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            return True
        except Exception:
            return False
