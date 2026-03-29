#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  AGL Deep Protocol Analyzer — المحلل العميق للبروتوكولات             ║
║  Uses fine-tuned LLM for deep semantic protocol understanding        ║
╚══════════════════════════════════════════════════════════════════════╝

This module provides deep protocol analysis capabilities using a
specialized fine-tuned LLM. Unlike regex/keyword-based layers, this
module UNDERSTANDS protocol logic, business invariants, and complex
interactions between functions.

Integration points:
  1. Called by core.py as a new analysis layer
  2. Receives raw source code + existing pipeline findings
  3. Returns deep findings with exploit paths

Architecture:
  Source Code → Protocol Classification → Invariant Extraction
       ↓                                         ↓
  Function-level Audit → CEI Verification → Exploit Reasoning
       ↓                                         ↓
  Cross-validation with pipeline findings → Unified deep analysis
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger("agl.deep_analyzer")

# ═══════════════════════════════════════════════════════════════
# LLM COMMUNICATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_MODEL = "agl-solidity-expert"
FALLBACK_MODEL = "qwen2.5:7b-instruct"

SYSTEM_PROMPT = (
    "You are AGL-SEC, an elite smart contract security auditor specialized in "
    "Solidity/EVM vulnerability detection, DeFi protocol analysis, symbolic reasoning, "
    "and exploit path construction. Always respond with valid JSON."
)


def _query_ollama(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str | None = None,
    temperature: float = 0.3,
    timeout: int = 120,
) -> str | None:
    """Send a query to Ollama and get the response."""
    import requests

    model = model or os.environ.get("AGL_LLM_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("AGL_LLM_BASEURL", "http://localhost:11434")

    # Try chat API first, fallback to generate
    for endpoint, payload in [
        (
            f"{base_url}/api/chat",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            },
        ),
        (
            f"{base_url}/api/generate",
            {
                "model": model,
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
                "options": {"temperature": temperature},
            },
        ),
    ]:
        try:
            resp = requests.post(endpoint, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("message", {}).get("content", "")
                    or data.get("response", "")
                )
                if content and len(content) > 50:
                    return content
        except Exception as e:
            logger.debug("Ollama %s failed: %s", endpoint, e)
            continue

    # Fallback to non-specialized model
    if model != FALLBACK_MODEL:
        logger.info("Falling back to %s", FALLBACK_MODEL)
        return _query_ollama(prompt, system, model=FALLBACK_MODEL, timeout=timeout)

    return None


def _parse_json_response(raw: str) -> dict | list | None:
    """Extract JSON from LLM response (handles markdown code blocks)."""
    if not raw:
        return None

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from code block
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object/array
    for pattern in [r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', r'\[.*\]']:
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    return None


# ═══════════════════════════════════════════════════════════════
# DEEP ANALYSIS TASKS
# ═══════════════════════════════════════════════════════════════


class DeepProtocolAnalyzer:
    """Deep protocol analysis using specialized LLM."""

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("AGL_LLM_MODEL", DEFAULT_MODEL)
        self._available = None

    def is_available(self) -> bool:
        """Check if the LLM is accessible."""
        if self._available is not None:
            return self._available
        try:
            import requests
            base_url = os.environ.get("AGL_LLM_BASEURL", "http://localhost:11434")
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                self._available = any(
                    self.model in m or FALLBACK_MODEL in m for m in models
                )
            else:
                self._available = False
        except Exception:
            self._available = False
        return self._available

    def analyze_contract(
        self,
        source: str,
        filepath: str = "",
        existing_findings: list[dict] | None = None,
    ) -> dict:
        """
        Full deep analysis of a contract.

        Returns:
            {
                "protocol_type": str,
                "invariants": list,
                "deep_findings": list[dict],
                "exploit_paths": list[dict],
                "false_positive_assessment": list[dict],
                "layers_used": ["deep_protocol_analyzer"],
            }
        """
        result = {
            "protocol_type": "unknown",
            "invariants": [],
            "deep_findings": [],
            "exploit_paths": [],
            "false_positive_assessment": [],
            "layers_used": ["deep_protocol_analyzer"],
            "analyzer_model": self.model,
        }

        if not self.is_available():
            logger.warning("LLM not available — skipping deep analysis")
            result["error"] = "LLM not available"
            return result

        # Truncate source for context window
        source_truncated = source[:6000]

        # ── Step 1: Protocol Classification ──
        ptype = self._classify_protocol(source_truncated)
        result["protocol_type"] = ptype

        # ── Step 2: Invariant Extraction ──
        invariants = self._extract_invariants(source_truncated, ptype)
        result["invariants"] = invariants

        # ── Step 3: Deep Vulnerability Analysis ──
        deep_findings = self._deep_vulnerability_scan(source_truncated, ptype, invariants)
        result["deep_findings"] = deep_findings

        # ── Step 4: Exploit Path Reasoning ──
        if deep_findings:
            exploits = self._reason_exploit_paths(source_truncated, deep_findings[:5])
            result["exploit_paths"] = exploits

        # ── Step 5: Cross-validate with existing findings ──
        if existing_findings:
            fp_assessment = self._assess_false_positives(
                source_truncated, existing_findings[:10]
            )
            result["false_positive_assessment"] = fp_assessment

        return result

    def _classify_protocol(self, source: str) -> str:
        """Identify protocol type (AMM, lending, vault, etc.)."""
        prompt = (
            "Classify this Solidity contract's protocol type.\n"
            "Categories: amm, lending, vault, governance, staking, bridge, token, unknown\n"
            "Respond with ONLY a JSON object: {\"type\": \"...\", \"confidence\": 0.0-1.0}\n\n"
            f"```solidity\n{source[:4000]}\n```"
        )
        raw = _query_ollama(prompt, model=self.model, timeout=60)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, dict):
            return parsed.get("type", "unknown")
        return "unknown"

    def _extract_invariants(self, source: str, protocol_type: str) -> list[dict]:
        """Extract business invariants that must hold."""
        prompt = (
            f"This is a {protocol_type} protocol. Extract ALL business invariants — "
            "properties that MUST hold true after every transaction.\n"
            "For each invariant, specify:\n"
            '- "property": the invariant in plain English\n'
            '- "formal": the invariant as a mathematical expression if possible\n'
            '- "violated_by": functions that could violate it\n'
            '- "critical": true if violation means fund loss\n\n'
            "Respond with JSON array of invariant objects.\n\n"
            f"```solidity\n{source[:5000]}\n```"
        )
        raw = _query_ollama(prompt, model=self.model, timeout=90)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, list):
            return parsed[:20]
        if isinstance(parsed, dict) and "invariants" in parsed:
            return parsed["invariants"][:20]
        return []

    def _deep_vulnerability_scan(
        self, source: str, protocol_type: str, invariants: list
    ) -> list[dict]:
        """Deep vulnerability analysis using LLM understanding."""
        invariant_text = "\n".join(
            f"  - {inv.get('property', inv) if isinstance(inv, dict) else inv}"
            for inv in invariants[:10]
        )
        prompt = (
            f"You are auditing a {protocol_type} protocol.\n"
            f"Known invariants:\n{invariant_text}\n\n"
            "Analyze the code for vulnerabilities. For EACH vulnerability found:\n"
            '- "title": concise vulnerability name\n'
            '- "severity": CRITICAL/HIGH/MEDIUM/LOW\n'
            '- "type": vulnerability category (reentrancy, access_control, logic_error, etc.)\n'
            '- "function": affected function name\n'
            '- "description": detailed explanation of WHY this is vulnerable\n'
            '- "invariant_violated": which invariant this breaks (if any)\n'
            '- "confidence": 0.0-1.0\n\n'
            "IMPORTANT: Only report REAL vulnerabilities with clear exploit paths. "
            "Do NOT report theoretical issues or standard patterns as vulnerabilities.\n"
            "Respond with JSON array.\n\n"
            f"```solidity\n{source[:5000]}\n```"
        )
        raw = _query_ollama(prompt, model=self.model, timeout=120)
        parsed = _parse_json_response(raw)

        findings = []
        if isinstance(parsed, list):
            findings = parsed
        elif isinstance(parsed, dict) and "vulnerabilities" in parsed:
            findings = parsed["vulnerabilities"]

        # Normalize findings
        normalized = []
        for f in findings[:15]:
            if not isinstance(f, dict):
                continue
            normalized.append({
                "title": f.get("title", "Unknown"),
                "severity": f.get("severity", "MEDIUM"),
                "type": f.get("type", "unknown"),
                "function": f.get("function", "unknown"),
                "description": f.get("description", ""),
                "invariant_violated": f.get("invariant_violated", None),
                "confidence": min(1.0, max(0.0, float(f.get("confidence", 0.5)))),
                "source": "deep_protocol_analyzer",
            })
        return normalized

    def _reason_exploit_paths(
        self, source: str, findings: list[dict]
    ) -> list[dict]:
        """Reason about concrete exploit paths for each finding."""
        findings_text = json.dumps(findings[:5], indent=2)
        prompt = (
            "Given these vulnerabilities, construct CONCRETE exploit paths.\n"
            "For each exploit:\n"
            '- "vulnerability": which finding this exploits\n'
            '- "steps": array of ordered attack steps (be SPECIFIC with function calls)\n'
            '- "profit_source": where the profit comes from\n'
            '- "prerequisites": what the attacker needs\n'
            '- "estimated_profit": rough estimate\n'
            '- "poc_sketch": Solidity code sketch for the attack contract\n\n'
            f"Vulnerabilities:\n{findings_text}\n\n"
            f"Contract:\n```solidity\n{source[:4000]}\n```\n\n"
            "Respond with JSON array."
        )
        raw = _query_ollama(prompt, model=self.model, timeout=120)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, list):
            return parsed[:10]
        if isinstance(parsed, dict) and "exploits" in parsed:
            return parsed["exploits"][:10]
        return []

    def _assess_false_positives(
        self, source: str, existing_findings: list[dict]
    ) -> list[dict]:
        """Assess whether existing pipeline findings are real or false positives."""
        findings_text = json.dumps(
            [
                {
                    "title": f.get("title", ""),
                    "severity": f.get("severity", ""),
                    "type": f.get("type", ""),
                    "description": str(f.get("description", ""))[:200],
                }
                for f in existing_findings[:10]
            ],
            indent=2,
        )
        prompt = (
            "The AGL Security Tool pipeline detected these findings. "
            "For EACH finding, determine if it's a TRUE positive or FALSE positive.\n"
            "Consider:\n"
            "- Does the code actually have this vulnerability?\n"
            "- Are there guards/modifiers that prevent exploitation?\n"
            "- Is the severity rating accurate?\n\n"
            "For each:\n"
            '- "title": the finding title\n'
            '- "verdict": "TRUE_POSITIVE" or "FALSE_POSITIVE"\n'
            '- "reasoning": WHY it is or isn\'t exploitable\n'
            '- "adjusted_severity": corrected severity if different\n\n'
            f"Findings:\n{findings_text}\n\n"
            f"Contract:\n```solidity\n{source[:4000]}\n```\n\n"
            "Respond with JSON array."
        )
        raw = _query_ollama(prompt, model=self.model, timeout=90)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "assessments" in parsed:
            return parsed["assessments"]
        return []

    def quick_scan(self, source: str) -> list[dict]:
        """Fast single-pass vulnerability scan (less thorough, faster)."""
        prompt = (
            "Quick security scan of this Solidity contract. "
            "List ONLY HIGH/CRITICAL vulnerabilities with clear exploit paths.\n"
            "For each:\n"
            '- "title", "severity", "function", "description", "exploit_summary"\n'
            "Respond with JSON array. If secure, return empty array [].\n\n"
            f"```solidity\n{source[:6000]}\n```"
        )
        raw = _query_ollama(prompt, model=self.model, timeout=90)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, list):
            return [
                {**f, "source": "deep_protocol_analyzer_quick"}
                for f in parsed if isinstance(f, dict)
            ]
        return []


# ═══════════════════════════════════════════════════════════════
# PIPELINE INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════


def integrate_deep_findings(
    pipeline_results: dict,
    deep_results: dict,
) -> dict:
    """Merge deep analysis findings into pipeline results."""
    if not deep_results or "error" in deep_results:
        return pipeline_results

    # Add deep findings to unified findings
    unified = pipeline_results.get("unified_findings", [])
    for finding in deep_results.get("deep_findings", []):
        # Convert to pipeline format
        unified.append({
            "title": finding.get("title", "Deep Analysis Finding"),
            "severity": finding.get("severity", "MEDIUM"),
            "type": finding.get("type", "logic_error"),
            "description": finding.get("description", ""),
            "source": "deep_protocol_analyzer",
            "function": finding.get("function", ""),
            "probability": finding.get("confidence", 0.5),
            "invariant_violated": finding.get("invariant_violated"),
        })

    pipeline_results["unified_findings"] = unified
    pipeline_results["deep_analysis"] = {
        "protocol_type": deep_results.get("protocol_type", "unknown"),
        "invariants_count": len(deep_results.get("invariants", [])),
        "exploit_paths_count": len(deep_results.get("exploit_paths", [])),
        "fp_assessed": len(deep_results.get("false_positive_assessment", [])),
    }

    # Add exploit paths
    if deep_results.get("exploit_paths"):
        pipeline_results.setdefault("exploit_paths", []).extend(
            deep_results["exploit_paths"]
        )

    # Add false positive assessments
    if deep_results.get("false_positive_assessment"):
        pipeline_results["fp_assessment"] = deep_results["false_positive_assessment"]

    if "deep_protocol_analyzer" not in pipeline_results.get("layers_used", []):
        pipeline_results.setdefault("layers_used", []).append("deep_protocol_analyzer")

    return pipeline_results
