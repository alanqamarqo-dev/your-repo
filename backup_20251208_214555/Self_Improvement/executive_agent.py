from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


def _default_queue_path() -> Path:
    """
    Returns the default task queue path. Can be overridden with
    the `AGL_TASK_QUEUE_PATH` environment variable (useful for tests).
    """
    env_path = os.getenv("AGL_TASK_QUEUE_PATH")
    if env_path:
        return Path(env_path)
    root = Path(__file__).resolve().parents[1]
    return root / "artifacts" / "task_queue.jsonl"


TASK_QUEUE_PATH: Path = _default_queue_path()


@dataclass
class TaskItem:
    """
    Representation of a single task in the executive queue.
    """
    project_id: str
    task_id: str
    description: str
    priority: float = 0.5
    status: str = "pending"  # pending / running / done / error
    result_summary: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TaskItem":
        return cls(
            project_id=data.get("project_id", ""),
            task_id=data.get("task_id", ""),
            description=data.get("description", ""),
            priority=float(data.get("priority", 0.5)),
            status=data.get("status", "pending"),
            result_summary=data.get("result_summary"),
        )


def load_task_queue(path: Optional[Path] = None) -> List[TaskItem]:
    """
    Read the task queue from a JSONL file.
    """
    p = path or TASK_QUEUE_PATH
    if not p.exists():
        return []

    tasks: List[TaskItem] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                tasks.append(TaskItem.from_dict(data))
            except Exception:
                # ignore malformed lines
                continue
    return tasks


def save_task_queue(tasks: List[TaskItem], path: Optional[Path] = None) -> None:
    """
    Save the task queue to a JSONL file (overwrites).
    """
    p = path or TASK_QUEUE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for task in tasks:
            json.dump(asdict(task), f, ensure_ascii=False)
            f.write("\n")


def enqueue_task(
    project_id: str,
    task_id: str,
    description: str,
    priority: float = 0.5,
    path: Optional[Path] = None,
) -> TaskItem:
    """
    Add a new task to the queue and persist.
    """
    tasks = load_task_queue(path)
    item = TaskItem(
        project_id=project_id,
        task_id=task_id,
        description=description,
        priority=priority,
        status="pending",
    )
    tasks.append(item)
    save_task_queue(tasks, path)
    return item


def run_executive_once(
    max_tasks: int = 1,
    queue_path: Optional[Path] = None,
) -> int:
    """
    Run a single executive loop:
    - pick highest-priority pending tasks
    - call `agl_pipeline` for each
    - update status/result and persist

    Returns the number of tasks executed in this run.
    """
    # delayed import so tests can monkeypatch Knowledge_Graph.agl_pipeline
    from Self_Improvement.Knowledge_Graph import agl_pipeline  # type: ignore

    p = queue_path or TASK_QUEUE_PATH
    tasks = load_task_queue(p)

    pending: List[TaskItem] = [t for t in tasks if t.status == "pending"]
    if not pending:
        return 0

    pending_sorted = sorted(pending, key=lambda t: t.priority, reverse=True)
    to_run = pending_sorted[: max_tasks]

    executed = 0
    for task in to_run:
        task.status = "running"
        try:
            question = f"[PROJECT {task.project_id}] {task.description}"
            result = agl_pipeline(question)

            if isinstance(result, dict):
                answer_text = str(result.get("answer") or "")
            else:
                answer_text = str(result)

            if not answer_text:
                answer_text = "(no answer returned)"

            task.result_summary = answer_text[:400]
            task.status = "done"
        except Exception as exc:  # noqa: BLE001
            task.result_summary = f"EXEC_ERROR: {exc}"
            task.status = "error"
        executed += 1

    save_task_queue(tasks, p)
    return executed
