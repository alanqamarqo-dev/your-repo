# -*- coding: utf-8 -*-
"""
AGL_UI_v2 — واجهة رسومية متقدمة لـ AGL
المزايا:
- تشغيل مهمة AGL من الواجهة مع تقرير
- عرض نتائج آخر تقرير (درجات المحركات + الثقة)
- رسم تاريخ الثقة من كل تقارير reports/*.json
- عرض السجل logs/agl.log
"""

import os, sys, json, glob, subprocess, time, threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- matplotlib + TkAgg setup (must be before pyplot imports) ---
try:
    import matplotlib
    matplotlib.use("TkAgg")  # important for Tkinter embedding
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    # (optional) Arabic-capable font preferences
    from matplotlib import rcParams
    rcParams['font.family'] = ['Segoe UI', 'Tahoma', 'Arial']
except Exception:
    Figure = None
    FigureCanvasTkAgg = None

# ───────────────────────── إعدادات قابلة للتعديل ─────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PYTHON_EXE  = sys.executable  # استخدم بايثون الحالي تلقائياً
AGL_SCRIPT  = os.path.join(PROJECT_ROOT, "AGL.py")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
LOG_PATH    = os.path.join(PROJECT_ROOT, "logs", "agl.log")
LAST_REPORT = os.path.join(REPORTS_DIR, "last_run.json")

# تأكد من وجود مجلد التقارير
os.makedirs(REPORTS_DIR, exist_ok=True)


def read_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": str(e)}


def list_report_files():
    files = glob.glob(os.path.join(REPORTS_DIR, "*.json"))
    # استثنِ ملفات مؤقتة إن وجدت
    files = [f for f in files if os.path.isfile(f)]
    # حاول ترتيبها بحسب timestamp داخل الملف، وإلا فبتاريخ الملف
    def keyf(p):
        try:
            data = read_json_safe(p)
            ts = data.get("timestamp", None)
            return float(ts) if ts else os.path.getmtime(p)
        except Exception:
            return os.path.getmtime(p)
    return sorted(files, key=keyf)


def parse_engine_scores(report):
    """إرجاع dict {'engine': score} من التقرير إن وجدت."""
    scores = {}
    try:
        # المسار 1: من solution.result لكل محرك
        res = report.get("solution", {}).get("result", {})
        for eng in ("mathematical_brain", "quantum_processor", "code_generator", "protocol_designer"):
            eng_obj = res.get(eng, {})
            # قد يكون الشكل القديم/الجديد
            s = eng_obj.get("score")
            if s is None:
                # مسار بديل: من report['signals']
                s = report.get("signals", {}).get(eng, {}).get("score")
            if s is not None:
                scores[eng] = float(s)
        # fallback: من report['signals'] كاملة
        if not scores and "signals" in report:
            for eng, info in report["signals"].items():
                try:
                    scores[eng] = float(info.get("score", 0.0))
                except Exception:
                    pass
    except Exception:
        pass
    return scores


def parse_confidence(report):
    return report.get("confidence_score") or report.get("solution", {}).get("confidence")


def format_pct(x):
    try:
        return f"{float(x)*100:.2f}%"
    except Exception:
        return "—"


class AGLUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AGL UI v2")
        self.geometry("1100x720")
        try:
            # تحسين عرض العربية في بعض الأنظمة
            import tkinter.font as tkfont
            try:
                tkfont.nametofont("TkDefaultFont").configure(family="Segoe UI", size=10)
            except Exception:
                # best-effort, ignore if font not available
                pass
        except Exception:
            pass

        self._build_layout()
        self._load_last_report()
        self._plot_conf_history()
        self._hook_shortcuts()

    # ───────────── واجهة المستخدم ─────────────
    def _build_layout(self):
        topbar = ttk.Frame(self, padding=8)
        topbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(topbar, text="المهمة:").pack(side=tk.RIGHT)
        self.task_var = tk.StringVar(value="حل نظام المعادلات التفاضلية")
        task_entry = ttk.Entry(topbar, textvariable=self.task_var, width=60, justify="right")
        task_entry.pack(side=tk.RIGHT, padx=6)

        self.run_btn = ttk.Button(topbar, text="تشغيل", command=self.run_task_clicked)
        self.run_btn.pack(side=tk.RIGHT, padx=6)

        self.refresh_btn = ttk.Button(topbar, text="تحديث", command=self.refresh_clicked)
        self.refresh_btn.pack(side=tk.RIGHT, padx=6)

        self.open_report_btn = ttk.Button(topbar, text="فتح تقرير...", command=self.open_report_dialog)
        self.open_report_btn.pack(side=tk.RIGHT, padx=6)

        # معلومات عامة
        info = ttk.Frame(self, padding=(8,0))
        info.pack(side=tk.TOP, fill=tk.X)
        self.lbl_report = ttk.Label(info, text="لا يوجد تقرير محمّل.", anchor="w")
        self.lbl_report.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # تقسيم علوي/سفلي
        main = ttk.Panedwindow(self, orient=tk.VERTICAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # القسم العلوي: محركات + الرسم العمودي
        upper = ttk.Panedwindow(main, orient=tk.HORIZONTAL)
        main.add(upper, weight=3)

        # جدول/نص النتائج
        left = ttk.Frame(upper)
        upper.add(left, weight=2)

        cols = ("engine","score","confidence","status")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree.heading(c, text={"engine":"المحرك","score":"الدرجة","confidence":"الثقة","status":"الحالة"}[c])
            self.tree.column(c, anchor="center", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # ملخص الثقة
        bottom_left = ttk.Frame(left, padding=6)
        bottom_left.pack(fill=tk.X)
        self.lbl_conf = ttk.Label(bottom_left, text="الثقة: —")
        self.lbl_conf.pack(side=tk.LEFT)

        # الرسم: أعمدة للمحركات
        right = ttk.Frame(upper)
        upper.add(right, weight=3)
        # initialize plotting area once
        if Figure:
            try:
                self._init_plot(parent=right, which=1)
            except Exception:
                self.fig1 = None
                self.ax1 = None
                self.canvas1 = None
        else:
            ttk.Label(right, text='matplotlib غير مثبت؛ لا يمكن عرض الرسم').pack(padx=10, pady=10)

        # القسم السفلي: تاريخ الثقة + السجل
        lower = ttk.Panedwindow(main, orient=tk.HORIZONTAL)
        main.add(lower, weight=2)

        # الرسم الخطي لتاريخ الثقة
        conf_frame = ttk.Frame(lower)
        lower.add(conf_frame, weight=3)
        # initialize confidence history plot once
        if Figure:
            try:
                self._init_plot(parent=conf_frame, which=2)
            except Exception:
                self.fig2 = None
                self.ax2 = None
                self.canvas2 = None
        else:
            ttk.Label(conf_frame, text='matplotlib غير مثبت؛ لا يمكن عرض الرسم').pack(padx=10, pady=10)

        # عارض السجل
        log_frame = ttk.Frame(lower)
        lower.add(log_frame, weight=4)
        ttk.Label(log_frame, text="سجل النظام (logs/agl.log):").pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=10, wrap="none")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self._load_log()

    def _hook_shortcuts(self):
        self.bind("<F5>", lambda e: self.refresh_clicked())
        self.bind("<Control-r>", lambda e: self.refresh_clicked())
        self.bind("<Control-Return>", lambda e: self.run_task_clicked())

    # --- Plot initialization and update helpers ---
    def _init_plot(self, parent, which=1):
        """Create figure/axis/canvas once and attach to parent frame.
        which: 1 -> engine bar chart, 2 -> confidence history
        """
        if Figure is None:
            return
        if which == 1:
            self.fig1 = Figure(figsize=(5,3), dpi=100)
            self.ax1 = self.fig1.add_subplot(111)
            self.ax1.set_title("درجات المحركات")
            self.ax1.set_ylim(0, 1)
            self.ax1.grid(True, alpha=0.25)
            self.canvas1 = FigureCanvasTkAgg(self.fig1, master=parent) # type: ignore
            self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            self.fig2 = Figure(figsize=(5,2.8), dpi=100)
            self.ax2 = self.fig2.add_subplot(111)
            self.ax2.set_title("تاريخ الثقة (من التقارير)")
            self.canvas2 = FigureCanvasTkAgg(self.fig2, master=parent) # type: ignore
            self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_plot(self, which=1, scores=None, xs=None, ys=None):
        """Clear and redraw the requested plot.
        - which==1: redraw engine bar chart using 'scores' dict
        - which==2: redraw confidence history using xs, ys lists
        """
        try:
            if which == 1:
                if not hasattr(self, 'ax1') or self.ax1 is None:
                    return
                self.ax1.clear()
                self.ax1.set_title("درجات المحركات")
                self.ax1.set_ylim(0, 1)
                if scores:
                    engines = list(scores.keys())
                    vals = [scores[k] for k in engines]
                    self.ax1.bar(engines, vals)
                    self.ax1.set_xticklabels(engines, rotation=20)
                else:
                    self.ax1.text(0.5, 0.5, "لا توجد بيانات محركات", ha="center", va="center")
                try:
                    self.canvas1.draw_idle() # type: ignore
                except Exception:
                    pass
            else:
                if not hasattr(self, 'ax2') or self.ax2 is None:
                    return
                self.ax2.clear()
                self.ax2.set_title("تاريخ الثقة (من التقارير)")
                if ys and xs:
                    self.ax2.plot(xs, ys, marker="o")
                    self.ax2.set_ylim(0, 1)
                else:
                    self.ax2.text(0.5, 0.5, "لا توجد تقارير كافية", ha="center", va="center")
                try:
                    self.fig2.autofmt_xdate() # type: ignore
                except Exception:
                    pass
                try:
                    self.canvas2.draw_idle() # type: ignore
                except Exception:
                    pass
        except Exception:
            return

    # ───────────── منطق التشغيل والقراءة ─────────────
    def run_task_clicked(self):
        task = self.task_var.get().strip()
        if not task:
            messagebox.showwarning("تحذير", "يرجى إدخال مهمة.")
            return
        if not os.path.isfile(AGL_SCRIPT):
            messagebox.showerror("خطأ", f"لم يتم العثور على {AGL_SCRIPT}")
            return

        # نبين حالة المعالجة ولا نجمد الواجهة
        self.run_btn.config(state="disabled")
        self.run_btn.update()

        def worker():
            try:
                cmd = [PYTHON_EXE, AGL_SCRIPT, "--task", task, "--report", LAST_REPORT]
                # ضبط بيئة UTF-8 للسلامة
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8-sig"
                proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding="utf-8-sig", errors="replace")
                output = proc.stdout
                self._append_loglike(f"\n$ {' '.join(cmd)}\n{output}\n")
                # تحديث العرض
                self.after(100, self._after_run_success)
            except Exception as e:
                self.after(100, lambda: messagebox.showerror("خطأ تشغيل", str(e)))
            finally:
                self.after(100, lambda: self.run_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _after_run_success(self):
        self._load_last_report()
        self._plot_conf_history()
        messagebox.showinfo("تم", "تم تنفيذ المهمة وتحديث التقرير.")

    def refresh_clicked(self):
        self._load_last_report()
        self._plot_conf_history()
        self._load_log()

    def open_report_dialog(self):
        path = filedialog.askopenfilename(
            title="اختر تقرير JSON",
            initialdir=REPORTS_DIR,
            filetypes=[("JSON files","*.json"),("All files","*.*")]
        )
        if path:
            self._load_report(path)

    # ───────────── التحميل والعرض ─────────────
    def _load_last_report(self):
        if os.path.isfile(LAST_REPORT):
            self._load_report(LAST_REPORT)
        else:
            self.lbl_report.config(text="لا يوجد reports/last_run.json بعد.")
            self._fill_table({}, None)
            try:
                self._plot_engines({})
            except Exception:
                pass

    def _load_report(self, path):
        data = read_json_safe(path)
        if "__error__" in data:
            messagebox.showerror("خطأ قراءة", f"تعذر قراءة التقرير:\n{data['__error__']}")
            return
        ts = data.get("timestamp")
        try:
            ts_f = float(ts) if ts is not None else None
        except Exception:
            ts_f = None
        ts_text = datetime.fromtimestamp(ts_f).strftime("%Y-%m-%d %H:%M:%S") if ts_f else "—"
        conf = parse_confidence(data)
        scores = parse_engine_scores(data)
        self.lbl_report.config(text=f"تقرير: {os.path.basename(path)} | الوقت: {ts_text} | الثقة: {format_pct(conf)}")
        self._fill_table(data.get("signals", {}), conf)
        self._plot_engines(scores)

    def _fill_table(self, signals, conf):
        # امسح
        for i in self.tree.get_children():
            self.tree.delete(i)
        # أضف
        if isinstance(signals, dict) and signals:
            for eng, info in signals.items():
                score = info.get("score", "—")
                conf_i = info.get("confidence", "—")
                status = "ok" if info.get("ok") else "not_ok"
                self.tree.insert("", "end", values=(eng, score, conf_i, status))
        else:
            # إن لم توجد إشارات، حاول من solution.result
            self.tree.insert("", "end", values=("—","—","—","—"))

        self.lbl_conf.config(text=f"الثقة الإجمالية: {format_pct(conf)}")

    def _plot_engines(self, scores):
        # Delegate to _update_plot which clears and redraws safely
        try:
            self._update_plot(which=1, scores=scores)
        except Exception:
            return

    def _plot_conf_history(self):
        files = list_report_files()
        xs, ys = [], []
        for p in files:
            d = read_json_safe(p)
            c = parse_confidence(d)
            t = d.get("timestamp") or os.path.getmtime(p)
            if c is not None:
                xs.append(datetime.fromtimestamp(float(t)))
                ys.append(float(c))
        # Delegate to _update_plot to redraw confidence history
        try:
            self._update_plot(which=2, xs=xs, ys=ys)
        except Exception:
            return

    def _load_log(self):
        self.log_text.delete("1.0", tk.END)
        if os.path.isfile(LOG_PATH):
            try:
                with open(LOG_PATH, "r", encoding="utf-8-sig", errors="replace") as f:
                    self.log_text.insert(tk.END, f.read())
            except Exception as e:
                self.log_text.insert(tk.END, f"[خطأ قراءة السجل] {e}\n")
        else:
            self.log_text.insert(tk.END, "لا يوجد logs/agl.log بعد.\n")

    def _append_loglike(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)


if __name__ == "__main__":
    # تحسين مخرجات الكونسول في ويندوز
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

    app = AGLUI()
    app.mainloop()
