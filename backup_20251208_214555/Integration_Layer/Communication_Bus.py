# Integration_Layer/Communication_Bus.py
class CommunicationBus:
    def route_messages(self, source, destination, message):
        """توجيه الرسائل بين المكونات"""
        return f"رسالة من {source} إلى {destination}: {message}"

    def coordinate_components(self, partial_solutions, purpose=None, fusion_weights=None):
        """Aggregate partial solutions returned by core engines.

        partial_solutions: list of dicts with keys 'engine', 'result', 'confidence'
        Returns a merged dict with combined 'result' and an overall 'confidence'.
        """
        if not partial_solutions:
            return {"result": None, "confidence": 0.0, "details": []}

        combined = {
            "result": {},
            "confidence": 0.0,
            "details": []
        }
        # fusion_weights: mapping engine->weight, default weight=1.0
        weights = fusion_weights or {}
        fused_score = 0.0
        total_w = 0.0

        # Expect partial_solutions to be a dict mapping engine->payload OR a list of payloads
        # Normalize to dict form: engine->payload
        normalized = {}
        if isinstance(partial_solutions, dict):
            normalized = partial_solutions
        else:
            for p in partial_solutions:
                en = p.get('engine')
                if en:
                    normalized[en] = p

        # Merge results and compute weighted confidence using signals inside payloads
        for name, payload in normalized.items():
            try:
                # Merge result
                res = payload.get('result') if isinstance(payload, dict) else None
                if isinstance(res, dict):
                    for k, v in res.items():
                        if k not in combined['result']:
                            combined['result'][k] = v
                else:
                    combined['result'][name] = res

                # use score as base signal
                s = float((payload.get('score') if isinstance(payload, dict) else 0.0) or 0.0)
                w = float(weights.get(name, 1.0))
                fused_score += s * w
                total_w += w
                combined['details'].append({'engine': name, 'score': s, 'weight': w})
            except Exception:
                continue

        confidence = (fused_score / total_w) if total_w else 0.0
        combined['confidence'] = confidence
        combined['fusion'] = {'weights': weights}
        # Optionally include purpose/context to help downstream interpretation
        if purpose is not None:
            combined['purpose'] = purpose
        return combined