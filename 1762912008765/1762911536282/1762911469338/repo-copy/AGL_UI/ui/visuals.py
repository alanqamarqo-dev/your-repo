"""Visualization helpers for AGL UI.
Use matplotlib if available; otherwise provide graceful fallbacks.
"""
from __future__ import annotations
import os
import json
import tkinter as tk


def _load_confidence_history():
    # prefer reports/performance_history.json then data/experiences.jsonl
    hist = []
    rpt = os.path.join(os.getcwd(), 'reports', 'performance_history.json')
    if os.path.exists(rpt):
        try:
            with open(rpt, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                hist = data.get('history', [])
        except Exception:
            hist = []

    if not hist:
        exp = os.path.join(os.getcwd(), 'data', 'experiences.jsonl')
        if os.path.exists(exp):
            try:
                with open(exp, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, start=1):
                        try:
                            j = json.loads(line)
                            # try to pull confidence_score or confidence
                            c = j.get('confidence_score') or j.get('solution', {}).get('confidence') or j.get('performance_metrics', {}).get('confidence')
                            if c is None:
                                continue
                            hist.append({'run': i, 'confidence': float(c)})
                        except Exception:
                            continue
            except Exception:
                hist = []

    return hist


def show_confidence_history_tk(parent):
    """Open a TK window and plot confidence history if matplotlib available."""
    try:
        import matplotlib.pyplot as plt # type: ignore
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
    except Exception:
        top = tk.Toplevel(parent)
        top.title('Confidence History')
        tk.Label(top, text='matplotlib is not installed; cannot render chart').pack(padx=20, pady=20)
        return

    hist = _load_confidence_history()
    runs = [h.get('run', idx + 1) for idx, h in enumerate(hist)]
    confs = [h.get('confidence', 0.0) for h in hist]

    fig, ax = plt.subplots(figsize=(6, 3))
    if runs:
        ax.plot(runs, confs, marker='o')
        ax.set_xlabel('run')
        ax.set_ylabel('confidence')
        ax.set_ylim(0, 1)
        ax.grid(True)
    else:
        ax.text(0.5, 0.5, 'No history available', ha='center', va='center')

    top = tk.Toplevel(parent)
    top.title('Confidence History')
    canvas = FigureCanvasTkAgg(fig, master=top)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)


def show_engine_performance_tk(parent, report_data=None):
    """Plot bar chart of engine scores from report_data (dict) or from reports/last_run.json."""
    try:
        import matplotlib.pyplot as plt # type: ignore
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
    except Exception:
        top = tk.Toplevel(parent)
        top.title('Engine Performance')
        tk.Label(top, text='matplotlib is not installed; cannot render chart').pack(padx=20, pady=20)
        return

    if report_data is None:
        path = os.path.join(os.getcwd(), 'reports', 'last_run.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    report_data = json.load(f)
            except Exception:
                report_data = {}
        else:
            report_data = {}

    signals = report_data.get('signals') or report_data.get('solution', {}).get('signals') or {}
    engines = ['mathematical_brain', 'quantum_processor', 'code_generator', 'protocol_designer']
    scores = []
    for e in engines:
        v = signals.get(e) or {}
        try:
            scores.append(float(v.get('score') or v.get('confidence') or 0.0))
        except Exception:
            scores.append(0.0)

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(engines, scores, color=['#4c72b0', '#55a868', '#c44e52', '#8172b2'])
    ax.set_ylim(0, 1)
    ax.set_ylabel('score')
    ax.set_title('Engine performance')

    top = tk.Toplevel(parent)
    top.title('Engine Performance')
    canvas = FigureCanvasTkAgg(fig, master=top)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
