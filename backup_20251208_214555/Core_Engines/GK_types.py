from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class GKSource:
    uri: str
    title: str
    provider: str
    date: Optional[str] = None


@dataclass
class GKEvidence:
    text: str
    source: GKSource
    score: float = 0.0
    meta: Dict = None # type: ignore


@dataclass
class GKFact:
    subject: str
    predicate: str
    obj: str
    confidence: float
    provenance: List[GKEvidence]


@dataclass
class GKQuery:
    text: str
    language: str = "auto"
    intent: str = "fact_query"


@dataclass
class GKAnswer:
    answer_text: str
    confidence: float
    supporting_facts: List[GKFact]
    contradictions: List[GKFact]
