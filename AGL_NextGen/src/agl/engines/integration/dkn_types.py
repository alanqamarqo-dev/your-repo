from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import uuid


@dataclass
class Signal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""         # example: 'task:new', 'claim', 'metric', 'plan', 'xfer'
    payload: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0      # salience/priority
    ts: float = field(default_factory=time.time)
    source: str = ""        # engine/layer name
    correlation_id: Optional[str] = None


@dataclass
class Claim:
    kind: str               # 'constraint' | 'metric' | 'plan' | 'hypothesis' | 'answer'
    content: Dict[str, Any] # structured JSON
    confidence: float
    relevance: float
    source: str
    ts: float = field(default_factory=time.time)
