from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from Self_Improvement import projects
from Self_Improvement.executive_agent import run_executive_once

ARTIFACTS_DIR = Path(os.getenv("AGL_ARTIFACTS_DIR", "artifacts"))
LONG_TERM_PROJECTS_PATH = ARTIFACTS_DIR / "long_term_projects.jsonl"


def _ensure_artifacts_dir():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class LongTermProjectConfig:
    project_id: str
    goal: str
    horizon_days: int
    daily_task_budget: int
    created_ts: float
    last_tick_ts: Optional[float] = None
    total_ticks: int = 0
    active: bool = True


def _append_long_term_config(cfg: LongTermProjectConfig):
    _ensure_artifacts_dir()
    with LONG_TERM_PROJECTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(cfg), ensure_ascii=False) + "\n")


def load_long_term_configs() -> List[LongTermProjectConfig]:
    if not LONG_TERM_PROJECTS_PATH.exists():
        return []
    rows: List[LongTermProjectConfig] = []
    with LONG_TERM_PROJECTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append(LongTermProjectConfig(**data))
    return rows


def start_long_term_project(
    goal: str,
    horizon_days: int = 7,
    daily_task_budget: int = 3,
    store: Optional[projects.ProjectStore] = None,
) -> LongTermProjectConfig:
    """Create a long-term project and persist its config.

    Uses `projects.create_project` to persist an initial project record and
    appends a config row to `long_term_projects.jsonl`.
    """
    if store is None:
        store = projects.ProjectStore()

    # generate a stable project id
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    # create the project via projects API
    proj = projects.create_project(project_id=project_id, goal=goal)

    # add an initial analysis task
    try:
        projects.add_task(project_id=proj.id, task_id=f"task-{uuid.uuid4().hex[:6]}", description=f"Analyse goal and split into subtasks: {goal}")
    except Exception:
        # best-effort: ignore task add failures
        pass

    cfg = LongTermProjectConfig(
        project_id=proj.id,
        goal=goal,
        horizon_days=horizon_days,
        daily_task_budget=daily_task_budget,
        created_ts=datetime.utcnow().timestamp(),
        last_tick_ts=None,
        total_ticks=0,
        active=True,
    )
    _append_long_term_config(cfg)
    return cfg


def _should_run_today(cfg: LongTermProjectConfig, now: Optional[datetime] = None) -> bool:
    if not cfg.active:
        return False
    if now is None:
        now = datetime.utcnow()
    if cfg.last_tick_ts is None:
        return True
    last = datetime.fromtimestamp(cfg.last_tick_ts)
    return now.date() > last.date()


def run_taskmaster_tick(
    store: Optional[projects.ProjectStore] = None,
    max_projects: int = 1,
    now: Optional[datetime] = None,
) -> int:
    """Run one tick of the taskmaster.

    - loads configs
    - selects up to `max_projects` configs that should run today
    - for each selected, calls `run_executive_once(max_tasks=cfg.daily_task_budget)`
    - updates last_tick_ts and total_ticks and rewrites the configs file
    Returns number of projects ticked.
    """
    _ensure_artifacts_dir()
    if store is None:
        store = projects.ProjectStore()
    cfgs = load_long_term_configs()
    if not cfgs:
        return 0
    if now is None:
        now = datetime.utcnow()

    selected: List[LongTermProjectConfig] = []
    for cfg in cfgs:
        if len(selected) >= max_projects:
            break
        if _should_run_today(cfg, now=now):
            selected.append(cfg)

    if not selected:
        return 0

    ticks_done = 0
    for cfg in selected:
        # call executive loop for this project (current design uses global queue)
        try:
            run_executive_once(max_tasks=cfg.daily_task_budget)
        except Exception:
            pass
        cfg.last_tick_ts = now.timestamp()
        cfg.total_ticks += 1
        ticks_done += 1

    # overwrite configs file with updated values
    with LONG_TERM_PROJECTS_PATH.open("w", encoding="utf-8") as f:
        for cfg in cfgs:
            f.write(json.dumps(asdict(cfg), ensure_ascii=False) + "\n")

    return ticks_done
