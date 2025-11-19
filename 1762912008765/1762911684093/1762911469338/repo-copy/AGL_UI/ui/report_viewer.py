import tkinter as tk
from tkinter import ttk
import json
import os
from . import visuals


class ReportViewer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._build()

    def _build(self):
        tk.Label(self, text='Last Report').pack(anchor='nw')
        self.text = tk.Text(self, wrap='none')
        self.text.pack(fill='both', expand=True)
        btn_frame = tk.Frame(self)
        btn_frame.pack(anchor='se')
        tk.Button(btn_frame, text='تحميل التقرير', command=self.refresh).pack(side='left', padx=4)
        tk.Button(btn_frame, text='عرض السجل', command=self.show_logs).pack(side='left', padx=4)
        tk.Button(btn_frame, text='عرض الرسم البياني للثقة', command=self._on_conf_chart).pack(side='left', padx=4)
        tk.Button(btn_frame, text='عرض أداء المحركات', command=self._on_engine_chart).pack(side='left', padx=4)
        tk.Button(btn_frame, text='السجل الكامل', command=self._on_full_log).pack(side='left', padx=4)
        self.summary_var = tk.StringVar()
        self.summary_label = tk.Label(self, textvariable=self.summary_var, anchor='w', justify='left', bg='#fff')
        self.summary_label.pack(fill='x')
        # intelligence pulse display
        self.pulse_var = tk.StringVar(value='—')
        self.pulse_label = tk.Label(self, textvariable=self.pulse_var, anchor='w', justify='left', bg='#fff', fg='#0b6623', font=('Segoe UI', 10, 'bold'))
        self.pulse_label.pack(fill='x')

    def refresh(self):
        path = os.path.join(os.getcwd(), 'reports', 'last_run.json')
        if not os.path.exists(path):
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, 'No report found')
            return
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, pretty)
            # update summary
            conf = data.get('confidence_score', data.get('confidence', 0.0))
            risk = data.get('safety', {}).get('risk_level', '?')
            gate = data.get('confidence_gate', {}).get('passed', False)
            self.summary_var.set(f"الثقة: {conf:.2%}    مستوى المخاطرة: {risk}")
            # color gate indicator on summary label
            if gate:
                self.summary_label.config(bg='#d4ffd4')
            else:
                self.summary_label.config(bg='#ffd4d4')
            # update intelligence pulse
            try:
                conf_f = float(conf or 0.0)
            except Exception:
                conf_f = 0.0
            opportunities = 0
            if data.get('verification_summary'):
                vs = data.get('verification_summary')
                opportunities += sum(1 for v in vs.values() if not v)
            if data.get('feedback'):
                opps = data.get('feedback', {}).get('gaps', {}).get('components', {})
                opportunities += sum(1 for c in opps.values() if c.get('needs_boost'))
            try:
                pulse = conf_f / (1.0 + float(opportunities) * 0.5)
            except Exception:
                pulse = 0.0
            self.pulse_var.set(f"{pulse:.3f} (conf={conf_f:.2f}, opp={opportunities})")
        except Exception as e:
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, f'Failed to load report: {e}')

    def show_logs(self):
        log_path = os.path.join(os.getcwd(), 'logs', 'agl.log')
        top = tk.Toplevel(self)
        top.title('AGL Log')
        text = tk.Text(top, wrap='none')
        text.pack(fill='both', expand=True)
        try:
            if not os.path.exists(log_path):
                text.insert('1.0', 'Log file not found')
                return
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text.insert('1.0', content)
        except Exception as e:
            text.insert('1.0', f'Failed to open log: {e}')

    def _on_conf_chart(self):
        try:
            visuals.show_confidence_history_tk(self.master)
        except Exception:
            pass

    def _on_engine_chart(self):
        try:
            # pass current report to visuals
            try:
                path = os.path.join(os.getcwd(), 'reports', 'last_run.json')
                with open(path, 'r', encoding='utf-8-sig') as f:
                    rpt = json.load(f)
            except Exception:
                rpt = None
            visuals.show_engine_performance_tk(self.master, rpt)
        except Exception:
            pass

    def _on_full_log(self):
        # open a scrollable log window with manual refresh
        log_path = os.path.join(os.getcwd(), 'logs', 'agl.log')
        top = tk.Toplevel(self)
        top.title('السجل الكامل - logs/agl.log')
        ctrl = tk.Frame(top)
        ctrl.pack(fill='x')
        btn_refresh = tk.Button(ctrl, text='تحديث', command=lambda: _refresh())
        btn_refresh.pack(side='left', padx=4, pady=4)
        auto_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(ctrl, text='تحديث تلقائي', variable=auto_var)
        chk.pack(side='left', padx=4, pady=4)

        text = tk.Text(top, wrap='none')
        text.pack(fill='both', expand=True)

        def _refresh():
            try:
                if not os.path.exists(log_path):
                    text.delete('1.0', tk.END)
                    text.insert('1.0', 'Log file not found')
                    return
                with open(log_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                    content = f.read()
                text.delete('1.0', tk.END)
                text.insert('1.0', content)
            except Exception as e:
                text.delete('1.0', tk.END)
                text.insert('1.0', f'Failed to open log: {e}')

        _refresh()

        def _maybe_auto():
            if auto_var.get():
                try:
                    _refresh()
                finally:
                    top.after(2000, _maybe_auto)

        top.after(2000, _maybe_auto)
