from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class ImprovementBudget:
    max_files_changed: int = 3
    max_total_bytes: int = 200_000
    allowed_suffixes: Tuple[str, ...] = (".py", ".md", ".json")

    def evaluate_steps(self, steps: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        files: List[str] = []
        total_bytes = 0

        for st in steps:
            if not isinstance(st, dict):
                continue
            op = str(st.get("op") or "")
            if op != "write_file":
                return {"approved": False, "reason": f"budget: unsupported op {op}"}

            path = str(st.get("path") or "")
            content = st.get("content")
            if not path:
                return {"approved": False, "reason": "budget: missing path"}
            if not any(path.endswith(suf) for suf in self.allowed_suffixes):
                return {"approved": False, "reason": f"budget: disallowed suffix for {path}"}

            if isinstance(content, str):
                total_bytes += len(content.encode("utf-8", errors="ignore"))
            else:
                return {"approved": False, "reason": f"budget: non-string content for {path}"}

            files.append(path)

        if len(set(files)) > self.max_files_changed:
            return {"approved": False, "reason": f"budget: too many files {len(set(files))}/{self.max_files_changed}"}
        if total_bytes > self.max_total_bytes:
            return {"approved": False, "reason": f"budget: too many bytes {total_bytes}/{self.max_total_bytes}"}

        return {"approved": True, "reason": "budget ok", "files": sorted(set(files)), "total_bytes": total_bytes}
