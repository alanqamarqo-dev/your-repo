from typing import Callable, Dict, List, Optional
from .dkn_types import Signal, Claim


class EngineAdapter:
    """Adapter that wraps an engine object and exposes a subscription surface.

    The engine object may be None (missing); the adapter should be tolerant and
    skip calls when the engine is not available.
    """

    def __init__(self, name: str, engine_obj: Optional[object], subscriptions: List[str], capabilities: List[str]):
        self.name = name
        self.engine = engine_obj
        self.subscriptions = set(subscriptions)
        self.capabilities = list(capabilities)

    def handles(self, topic: str) -> bool:
        return topic in self.subscriptions

    def on_signal(self, signal: Signal, graph, bus) -> None:
        # If engine missing, no-op but publish an error signal
        if self.engine is None:
            # publish a low-priority error for observability
            bus.publish(Signal(topic='error', payload={'msg': 'engine-missing'}, score=0.05, source=self.name))
            return

        # determine operation and call engine.process_task where possible
        op = self._decide_op(signal)
        try:
            # many engines accept process_task(dict)
            if hasattr(self.engine, 'process_task') and callable(getattr(self.engine, 'process_task')):
                res = self.engine.process_task({'op': op, 'params': signal.payload}) # type: ignore
            else:
                # fallback: try call with signal.payload
                res = self.engine(signal.payload) if callable(self.engine) else {}
        except Exception as e:
            bus.publish(Signal(topic='error', payload={'msg': str(e)}, score=0.01, source=self.name))
            return

        # convert results into Claims and store in the KnowledgeGraph (preferred)
        if isinstance(res, dict):
            # 1) free text or simple answer -> answer_piece
            text = res.get('text') or res.get('answer') or (res.get('answer_json') and res.get('answer_json').get('text') if isinstance(res.get('answer_json'), dict) else None) # type: ignore
            if text:
                graph.add_claim(Claim(
                    kind='answer_piece',
                    content={'text': text},
                    confidence=float(res.get('confidence', 0.65) or 0.65),
                    relevance=float(res.get('relevance', 0.70) or 0.70),
                    source=self.name
                ))

            # 2) structured fields -> map to claim kinds
            for k_json, kind in [
                ('constraints', 'constraint'),
                ('tradeoffs', 'tradeoff'),
                ('metrics', 'metric'),
                ('steps', 'plan_step'),
                ('xfer_link', 'xfer_link'),
                ('answer_json', 'answer_piece'),
            ]:
                if k_json in res and res[k_json]:
                    graph.add_claim(Claim(
                        kind=kind,
                        content={k_json: res[k_json]},
                        confidence=float(res.get('confidence', 0.70) or 0.70),
                        relevance=float(res.get('relevance', 0.70) or 0.70),
                        source=self.name
                    ))

            # 3) existing list-style claims/pieces
            for k in ('claims', 'pieces'):
                items = res.get(k)
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict):
                            kind = it.get('kind', 'answer_piece')
                            graph.add_claim(Claim(
                                kind=kind,
                                content=it.get('content', it),
                                confidence=float(it.get('confidence', 0.6) or 0.6),
                                relevance=float(it.get('relevance', 0.5) or 0.5),
                                source=self.name
                            ))

        else:
            # unknown response type — store as a raw claim
            graph.add_claim(Claim(
                kind='raw',
                content={'value': str(res)},
                confidence=0.1,
                relevance=0.1,
                source=self.name
            ))

    def _decide_op(self, signal: Signal) -> str:
        # Route task:new to engines that are answer-capable to ensure at least
        # one engine produces textual output early in the pipeline.
        if signal.topic == 'task:new' and 'prompt' in signal.payload:
            if self.name in ("Reasoning_Layer", "Hybrid_Reasoner", "Strategic_Thinking"):
                return 'answer'
            if self.name == 'Prompt_Composer_V2':
                return signal.payload.get('op', 'compose')
        return signal.payload.get('op', 'answer')
