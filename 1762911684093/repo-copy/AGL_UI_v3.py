# -*- coding: utf-8 -*-
"""
AGL_UI_v3.py
واجهة رسومية محسّنة لعرض وتشغيل نظام AGL
- تشغيل مهمة وكتابة تقرير JSON
- تشغيل ذكي: يحل/يولّد/يقيم ويعرض النتائج
- عرض درجات المحركات + الثقة الإجمالية
- رسم بياني مباشر لنتائج المحركات
- قراءة السجل مع دعم BOM (UTF-8-SIG)

المتطلبات القياسية: tkinter, json, subprocess, threading, matplotlib
"""

import os, sys, json, time, threading, subprocess, hashlib
from pathlib import Path
from typing import Optional, Callable
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# matplotlib嵌ادخال الرسم داخل Tk
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib import rcParams
    rcParams['font.family'] = ['Segoe UI', 'Tahoma', 'Arial']
except Exception:
    Figure = None
    FigureCanvasTkAgg = None

# -------- إعداد مسارات المشروع --------
ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
LOGS = ROOT / "logs"
ARTIFACTS = ROOT / "artifacts"
AGL_PY = ROOT / "AGL.py"  # نقطة التشغيل
DEFAULT_REPORT = REPORTS / "last_run.json"
LOGFILE = LOGS / "agl.log"

# تأكد من وجود المجلدات
for p in (REPORTS, LOGS, ARTIFACTS):
    p.mkdir(exist_ok=True)

# -------- أدوات مساعدة --------
def read_text_safely(path: Path, limit_lines: int = 4000) -> str:
    """قراءة ملف نصي بدعم UTF-8 و UTF-8-SIG لتجنّب BOM error."""
    if not path.exists():
        return ""
    data = None
    # جرّب UTF-8 بدون BOM
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            data = f.read()
    except UnicodeError:
        # جرّب UTF-8 مع BOM
        with path.open("r", encoding="utf-8-sig") as f:
            data = f.read()
    # تقليص الأسطر إذا كان ضخمًا
    if data is None:
        return ""
    lines = data.splitlines()
    if len(lines) > limit_lines:
        lines = lines[-limit_lines:]
    return "\n".join(lines)


def load_report(path: Path, post_load: Optional[Callable] = None) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            report = json.load(f)
            # call optional post-load hook with signals
            try:
                if post_load:
                    signals = (report or {}).get("signals", {})
                    try:
                        post_load(signals)
                    except Exception:
                        pass
            except Exception:
                pass
            return report
    except UnicodeDecodeError:
        # fallback: try without signature if there is an odd case
        try:
            with path.open("r", encoding="utf-8") as f:
                report = json.load(f)
                try:
                    if post_load:
                        signals = (report or {}).get("signals", {})
                        try:
                            post_load(signals)
                        except Exception:
                            pass
                except Exception:
                    pass
                return report
        except Exception:
            raise
    except Exception as e:
        messagebox.showerror("خطأ قراءة التقرير", str(e))
        return {}


def pretty_float(x):
    try:
        return f"{float(x):.4f}"
    except Exception:
        return "-"


def run_agl(task_text: str, report_path: Path = DEFAULT_REPORT) -> int:
    """تشغيل AGL.py من نفس بيئة بايثون الحالية لضمان الحزم."""
    if not AGL_PY.exists():
        messagebox.showerror("AGL.py غير موجود", f"لم يتم العثور على: {AGL_PY}")
        return 1
    # استخدم نفس المفسر الحالي
    py = sys.executable
    cmd = [
        py, str(AGL_PY),
        "--task", task_text,
        "--report", str(report_path)
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8-sig",
            errors="replace"
        )
        return proc.returncode
    except Exception as e:
        messagebox.showerror("فشل التشغيل", str(e))
        return 1


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# -------- الواجهة --------
class AGLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AGL Control Panel v3")
        self.geometry("1080x720")
        self.minsize(980, 640)

        self._build_ui()
        self._start_log_tailer()
        self.refresh_from_report()

    # --- بناء الواجهة
    def _build_ui(self):
        # أعلى: إدخال المهمة + الأزرار
        top = ttk.Frame(self, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="المهمة:").pack(side=tk.LEFT)
        self.task_var = tk.StringVar(value="حل نظام المعادلات التفاضلية")
        self.task_entry = ttk.Entry(top, textvariable=self.task_var, width=60)
        self.task_entry.pack(side=tk.LEFT, padx=6)

        ttk.Button(top, text="تشغيل", command=self.on_run).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="تشغيل ذكي", command=self.on_smart_run).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="فتح تقرير...", command=self.on_open_report).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="تحديث", command=self.refresh_from_report).pack(side=tk.LEFT, padx=3)

        # منتصف: جدول النتائج + الرسم البياني + ملخص
        middle = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        middle.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=6, padx=6)

        # يسار: جدول المحركات
        left = ttk.Frame(middle, padding=6)
        middle.add(left, weight=1)

        ttk.Label(left, text="نتائج المحركات", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("engine", "score", "confidence", "status")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=10)
        self.tree.heading("engine", text="المحرك")
        self.tree.heading("score", text="الدرجة")
        self.tree.heading("confidence", text="الثقة")
        self.tree.heading("status", text="الحالة")
        self.tree.column("engine", width=170)
        self.tree.column("score", width=100, anchor=tk.CENTER)
        self.tree.column("confidence", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=4)

        self.summary_lbl = ttk.Label(left, text="الثقة الإجمالية: -", font=("Segoe UI", 10))
        self.summary_lbl.pack(anchor="w", pady=(6, 0))

        # يمين: الرسم البياني
        right = ttk.Frame(middle, padding=6)
        middle.add(right, weight=1)

        ttk.Label(right, text="رسم درجات المحركات", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        # place a placeholder for the plot (we initialize after full UI build)
        if not Figure:
            ttk.Label(right, text='matplotlib غير مثبت؛ لا يمكن عرض الرسم').pack(padx=10, pady=10)

        # store a reference to the right frame so we can initialize the plot
        self._plot_parent = right

        # أسفل: سجل مباشر
        bottom = ttk.Frame(self, padding=6)
        bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)
        ttk.Label(bottom, text=f"سجل النظام ({LOGFILE})", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.log_box = ScrolledText(bottom, height=12, wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log_box.configure(font=("Consolas", 10))
        self.log_box.insert(tk.END, read_text_safely(LOGFILE))

        # شريط الحالة
        self.status_var = tk.StringVar(value="جاهز")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding=4)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # finally, initialize the plot now that the full UI exists
        try:
            if Figure and hasattr(self, '_plot_parent'):
                self._init_plot(parent=self._plot_parent, which=1)
        except Exception:
            # ensure attributes exist to avoid AttributeErrors elsewhere
            self.fig = getattr(self, 'fig', None)
            self.ax = getattr(self, 'ax', None)
            self.canvas = getattr(self, 'canvas', None)

    # plotting helpers
    def _init_plot(self, parent, which=1):
        if Figure is None:
            return
        if which == 1:
            self.fig = Figure(figsize=(5, 3), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.ax.set_ylim(0, 1)
            self.ax.set_ylabel("Score")
            self.ax.grid(True, alpha=0.25)
            self.canvas = FigureCanvasTkAgg(self.fig, master=parent) # type: ignore
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            # initial draw
            try:
                self.canvas.draw_idle()
            except Exception:
                pass
        else:
            # reserved for other plots if needed
            pass

    def _update_plot(self, signals_dict: dict):
        """
        signals_dict شكل متوقع:
        {
          "mathematical_brain": {"score": 0.92, ...},
          "quantum_processor": {"score": 0.60, ...},
          ...
        }
        """
        if not hasattr(self, 'fig') or not hasattr(self, 'ax') or self.ax is None:
            return

        labels = ["mathematical_brain", "quantum_processor", "code_generator", "protocol_designer"]

        def safe_score(name):
            try:
                v = signals_dict.get(name) or {}
                s = v.get("score")
                return float(s) if s is not None else 0.0
            except Exception:
                return 0.0

        values = [safe_score(n) for n in labels]

        try:
            # امسح الرسمة السابقة وارسم من جديد
            self.ax.clear()
            self.ax.bar(labels, values)
            self.ax.set_ylim(0, 1.0)
            self.ax.set_ylabel("Score")
            self.ax.set_title("درجات المحركات")
            self.ax.grid(True, alpha=0.3)
            try:
                self.fig.tight_layout() # type: ignore
            except Exception:
                pass

            # الأهم: أعد الرسم
            try:
                self.canvas.draw_idle() # type: ignore
            except Exception:
                pass
        except Exception:
            return

    # --- أحداث
    def on_run(self):
        task = self.task_var.get().strip()
        if not task:
            messagebox.showwarning("تنبيه", "الرجاء إدخال مهمة.")
            return
        self._run_in_thread(task, DEFAULT_REPORT)

    def on_smart_run(self):
        """تشغيل بمهمة موحّدة وإنتاج تقرير ثم تحديث العرض."""
        task = self.task_var.get().strip() or "حل نظام المعادلات التفاضلية"
        self._run_in_thread(task, DEFAULT_REPORT)

    def _run_in_thread(self, task: str, report_path: Path):
        self.status_var.set(f"يجري التنفيذ: {task} ...")
        def work():
            rc = run_agl(task, report_path)
            time.sleep(0.2)
            self.refresh_from_report()
            self.status_var.set("تم التنفيذ" if rc == 0 else f"انتهى مع كود {rc}")
        threading.Thread(target=work, daemon=True).start()

    def on_open_report(self):
        path = filedialog.askopenfilename(
            title="اختر تقرير JSON",
            initialdir=str(REPORTS),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        self.refresh_from_report(Path(path))

    # --- التحديث من التقرير
    def refresh_from_report(self, path: Path = DEFAULT_REPORT):
        rpt = load_report(path)
        if not rpt:
            self.summary_lbl.config(text="الثقة الإجمالية: لا يوجد تقرير")
            self._fill_table({})
            self._plot({})
            return

        # الثقة الإجمالية
        conf = rpt.get("confidence_score") or rpt.get("solution", {}).get("confidence")
        if conf is None:
            conf = "-"
        else:
            try:
                conf = float(conf)
            except Exception:
                pass
        self.summary_lbl.config(text=f"الثقة الإجمالية: {conf if isinstance(conf,str) else f'{conf:.4f}'}")

        # إشارات المحركات
        signals = rpt.get("signals") or rpt.get("solution", {}).get("result", {})
        # في حال كانت بنية مختلفة
        if isinstance(signals, dict) and "mathematical_brain" not in signals and "quantum_processor" not in signals:
            signals = rpt.get("signals", {})

        self._fill_table(signals)
        # update the engine plot from signals (safe redraw)
        try:
            self._update_plot(signals)
        except Exception:
            try:
                self._plot(signals)
            except Exception:
                pass

        # عرض جزء من التقرير في السجل (اختياري)
        try:
            snippet = json.dumps(rpt.get("solution", {}), ensure_ascii=False, indent=2)
            self.log_box.insert(tk.END, "\n\n[حل محدث]\n")
            self.log_box.insert(tk.END, snippet + "\n")
            self.log_box.see(tk.END)
        except Exception:
            pass

    def _fill_table(self, signals: dict):
        # امسح
        for row in self.tree.get_children():
            self.tree.delete(row)
        # أضف
        order = ["mathematical_brain", "quantum_processor", "code_generator", "protocol_designer"]
        nice = {
            "mathematical_brain": "mathematical_brain",
            "quantum_processor": "quantum_processor",
            "code_generator": "code_generator",
            "protocol_designer": "protocol_designer",
        }
        for k in order:
            s = signals.get(k, {}) if isinstance(signals, dict) else {}
            score = s.get("score", s.get("confidence", ""))
            conf = s.get("confidence", score)
            status = "ok" if s.get("ok") is True or s.get("status") == "ok" else (s.get("status") or "")
            self.tree.insert("", tk.END, values=(nice[k], pretty_float(score), pretty_float(conf), status))

    def _plot(self, signals: dict):
        if not self.fig:
            return
        self.ax.clear() # type: ignore
        self.ax.set_ylim(0, 1) # type: ignore
        self.ax.set_ylabel("Score") # type: ignore
        self.ax.grid(True, alpha=0.25) # type: ignore

        labels = ["math", "quantum", "codegen", "protocol"]
        keys = ["mathematical_brain", "quantum_processor", "code_generator", "protocol_designer"]
        vals = []
        for k in keys:
            v = 0.0
            if isinstance(signals, dict):
                s = signals.get(k, {})
                v = float(s.get("score", 0.0) or 0.0)
            vals.append(v)

        self.ax.bar(labels, vals) # type: ignore
        self.ax.set_title("Engine Scores") # type: ignore
        try:
            if FigureCanvasTkAgg:
                self.canvas.draw_idle() # type: ignore
        except Exception:
            pass

    # --- متابعة السجل باستمرار
    def _start_log_tailer(self):
        def follow():
            last = ""
            while True:
                try:
                    text = read_text_safely(LOGFILE, limit_lines=1200)
                    if text != last:
                        self.log_box.delete(1.0, tk.END)
                        self.log_box.insert(tk.END, text)
                        self.log_box.see(tk.END)
                        last = text
                except Exception:
                    pass
                time.sleep(1.0)
        threading.Thread(target=follow, daemon=True).start()


if __name__ == "__main__":
    app = AGLApp()
    app.mainloop()
