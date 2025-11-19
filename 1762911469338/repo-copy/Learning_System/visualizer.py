# -*- coding: utf-8 -*-
"""
Simple visualizer for AGL models (phase G)
Generates PNG plots comparing learned model curve.
"""
from __future__ import annotations
import json, os, math
from typing import Dict, Tuple
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


def _curve_fn(winner: str, a: float, b: float):
    if winner in ("ohm", "hooke", "k*x", "k*x + b"):
        # linear: y = a*x + b (b may be ~0)
        return lambda x: a * x + (b if winner != "k*x" else 0.0)
    if winner in ("poly2", "a*x**2"):
        # quadratic: y = a*x^2 + b (we treat 'poly2' like a*x^2 + b)
        return lambda x: a * (x**2) + b
    if winner in ("exp1",):
        # exponential: y ≈ b + exp(a*x)
        return lambda x: b + np.exp(a * x)
    if winner in ("power",):
        # power law: y ≈ A·x^B   (a= A, b = B)
        A, B = a, b
        return lambda x: A * (np.power(np.maximum(x, 1e-12), B))
    # fallback linear
    return lambda x: a * x + b


def _nice_range(xmin: float, xmax: float, n: int = 200) -> np.ndarray:
    if xmin == xmax:
        xmin, xmax = xmin - 1.0, xmax + 1.0
    if not np.isfinite([xmin, xmax]).all():
        xmin, xmax = 0.0, 1.0
    if xmax < xmin:
        xmin, xmax = xmax, xmin
    if xmax - xmin < 1e-12:
        xmax = xmin + 1.0
    pad = 0.05 * (xmax - xmin)
    return np.linspace(xmin - pad, xmax + pad, n)


def _read_csv_points(csv_path: str) -> Tuple[list, list]:
    xs = []
    ys = []
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as fh:
            r = csv.DictReader(fh)
            headers = [h.lower() for h in r.fieldnames or []]
            if 'x' in headers and 'y' in headers:
                for row in r:
                    try:
                        xs.append(float(row.get('x') or row.get('X'))) # type: ignore
                        ys.append(float(row.get('y') or row.get('Y'))) # type: ignore
                    except Exception:
                        continue
            else:
                cols = r.fieldnames or []
                for row in r:
                    try:
                        xval = float(row.get(cols[0])) # type: ignore
                        yval = float(row.get(cols[1])) # type: ignore
                        xs.append(xval)
                        ys.append(yval)
                    except Exception:
                        continue
    except Exception:
        return [], []
    return xs, ys


def render_model_png(result_path: str, out_png: str, title: str = "") -> Dict:
    """
    Read artifacts/.../results.json and render a PNG with the fitted curve.
    If CSV or inline samples are available, overlay the data points.
    Also save a PDF export. Returns dict with metadata.
    """
    with open(result_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Phase D newer files may wrap winner under 'ensemble'
    if "ensemble" in data and data["ensemble"].get("success"):
        r = data["ensemble"]["result"]
        winner = r.get("winner")
        params = r.get("params", {})
        a = float(params.get("a", 0.0))
        b = float(params.get("b", 0.0))
        rmse = float(r.get("rmse", float("nan")))
        n = int(r.get("n", 0))
    else:
        r0 = data.get("results", [])[0] if data.get("results") else {}
        winner = r0.get("candidate") or data.get("base") or "model"
        fit = r0.get("fit") or {}
        a = float(fit.get("a", 0.0))
        b = float(fit.get("b", 0.0))
        rmse = float(fit.get("rmse", float("nan")))
        n = int(fit.get("n", data.get("results", [{}])[0].get("n_samples", 0))) if fit else int(data.get("results", [{}])[0].get("n_samples", 0))

    xname = data.get("xname", "x")
    yname = data.get("yname", "y")
    base = data.get("base", os.path.basename(os.path.dirname(result_path)))
    fn = _curve_fn(winner, a, b)

    # Choose an x-range
    if winner == "exp1" and a != 0:
        tau = abs(1.0 / a) if a != 0 else 1.0
        xs = _nice_range(0.0, 5.0 * tau)
    elif winner == "power":
        xs = _nice_range(0.0, 10.0)
    else:
        xs = _nice_range(-3.0, 3.0)

    ys = fn(xs)

    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    # base plot
    plt.figure(figsize=(6, 4), dpi=140)
    plt.plot(xs, ys, linewidth=2, label=f"fit: {winner}")
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.title(title or f"{base}: {winner} (rmse={rmse:.4g}, n={n})")
    plt.grid(True)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()

    # save PDF export
    out_pdf = os.path.splitext(out_png)[0] + ".pdf"
    try:
        plt.figure(figsize=(6, 4), dpi=140)
        plt.plot(xs, ys, linewidth=2, label=f"fit: {winner}")
        plt.xlabel(xname)
        plt.ylabel(yname)
        plt.title(title or f"{base}: {winner} (rmse={rmse:.4g}, n={n})")
        plt.grid(True)
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(out_pdf)
    except Exception:
        out_pdf = out_png
    finally:
        try:
            plt.close()
        except Exception:
            pass

    # Attempt to find data points: inline samples, explicit csv path, or csv in same dir
    data_xs = []
    data_ys = []
    try:
        if isinstance(data.get('samples'), list) and len(data.get('samples')) > 0:
            for s in data.get('samples'):
                if isinstance(s, dict) and ('x' in s or 'X' in s) and ('y' in s or 'Y' in s):
                    try:
                        data_xs.append(float(s.get('x') or s.get('X'))) # type: ignore
                        data_ys.append(float(s.get('y') or s.get('Y'))) # type: ignore
                    except Exception:
                        continue

        if not data_xs:
            for key in ('data_path', 'data_file', 'csv'):
                p = data.get(key)
                if p and isinstance(p, str) and os.path.exists(p):
                    dx, dy = _read_csv_points(p)
                    if dx:
                        data_xs, data_ys = dx, dy
                        break

        if not data_xs:
            rp_dir = os.path.dirname(result_path)
            for f in os.listdir(rp_dir):
                if f.lower().endswith('.csv'):
                    dx, dy = _read_csv_points(os.path.join(rp_dir, f))
                    if dx:
                        data_xs, data_ys = dx, dy
                        break
    except Exception:
        data_xs, data_ys = [], []

    plotted_points = 0
    if data_xs:
        try:
            plt.figure(figsize=(6, 4), dpi=140)
            plt.plot(xs, ys, linewidth=2, label=f"fit: {winner}")
            plt.scatter(data_xs, data_ys, s=24, alpha=0.8, color='orange', label='data')
            plt.xlabel(xname)
            plt.ylabel(yname)
            plt.title(title or f"{base}: {winner} (rmse={rmse:.4g}, n={n})")
            plt.grid(True)
            plt.legend(loc="best")
            plt.tight_layout()
            plt.savefig(out_png)
            try:
                plt.savefig(out_pdf)
            except Exception:
                pass
            plotted_points = len(data_xs)
        except Exception:
            plotted_points = 0
        finally:
            try:
                plt.close()
            except Exception:
                pass

    return {
        "base": base,
        "winner": winner,
        "a": a, "b": b,
        "rmse": rmse, "n": n,
        "xname": xname, "yname": yname,
        "png": out_png, "pdf": out_pdf,
        "plotted_points": plotted_points
    }
