# Minimal Law Studio UI stub (Tkinter)
from tkinter import Frame, Label, Entry, Button, filedialog, Text
import json
import os

class LawStudioTab(Frame):
    def __init__(self, master, orchestrator):
        super().__init__(master)
        self.orch = orchestrator
        Label(self, text='Formula').grid(row=0, column=0)
        self.form_entry = Entry(self, width=40)
        self.form_entry.grid(row=0, column=1)
        Button(self, text='Load CSV', command=self._load_csv).grid(row=0, column=2)
        Button(self, text='Run Fit', command=self._run_fit).grid(row=1, column=0)
        Button(self, text='Save to KB', command=self._save_kb).grid(row=1, column=1)
        Button(self, text='Run Self-Learn', command=self._run_self_learn).grid(row=1, column=2)
        Button(self, text='Open Training Panel', command=self._open_training_panel).grid(row=1, column=3)
        self.output = Text(self, width=100, height=20)
        self.output.grid(row=2, column=0, columnspan=4)
        self.loaded_data = None
        self.last_report = None

    def _load_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV files','*.csv')])
        if not path:
            return
        import csv
        data = {}
        rows = []
        with open(path, 'r', encoding='utf-8-sig') as f:
            dr = csv.DictReader(f)
            for row in dr:
                # keep rows as dicts for the learner API; convert numeric values
                r = {}
                for k,v in row.items():
                    try:
                        r[k] = float(v)
                    except Exception:
                        r[k] = v
                    data.setdefault(k,[]).append(r[k])
                rows.append(r)
        self.loaded_data = { 'columns': data, 'rows': rows }
        self.output.insert('end', f'Loaded data from {path}\n')

    def _run_fit(self):
        formula = self.form_entry.get().strip()
        if not formula:
            self.output.insert('end','No formula provided\n')
            return
        # simple parse: expect y = a*x or y = a*x + b
        if not self.loaded_data or 'columns' not in self.loaded_data:
            self.output.insert('end', 'No data loaded\n')
            return
        cols = self.loaded_data['columns']
        col_names = list(cols.keys())
        if len(col_names) < 2:
            self.output.insert('end', 'Need at least two columns (y and x)\n')
            return
        y_name = col_names[0]
        x_name = col_names[1]
        res = None
        try:
            # convert to format expected by fit_model_auto: mapping of name->[values]
            from Learning_System.Law_Learner import fit_model_auto
            res = fit_model_auto(formula, y_name, x_name, cols)
            self.last_report = res
            self.output.insert('end', json.dumps(res, indent=2, ensure_ascii=False) + '\n')
        except Exception as e:
            self.output.insert('end', f'Fit failed: {e}\n')

    def _save_kb(self):
        if not self.last_report:
            self.output.insert('end', 'No report to save. Run Fit first.\n')
            return
        try:
            from Knowledge_Base.Law_Facts import save_law_fact
            import time
            key = f"ui_fact_{int(time.time())}"
            # include timestamp and confidence if gate present
            payload = { 'report': self.last_report, 'ts': int(time.time()) }
            save_law_fact(key, payload)
            self.output.insert('end','Saved to KB\n')
        except Exception as e:
            self.output.insert('end', f'KB save failed: {e}\n')

    def _run_self_learn(self):
        if not self.last_report:
            self.output.insert('end', 'No report available. Run Fit first.\n')
            return
        try:
            from Learning_System.Self_Learning import SelfLearning
            # prepare samples from loaded rows
            samples = self.loaded_data.get('rows') if self.loaded_data else None
            sl = SelfLearning()
            formula = self.form_entry.get().strip() or str(self.last_report)
            res = sl.run(formula, samples or [])
            self.output.insert('end', 'Self-learning produced:\n')
            self.output.insert('end', json.dumps(res, indent=2, ensure_ascii=False) + '\n')
        except Exception as e:
            self.output.insert('end', f'Self-learn failed: {e}\n')

    def _open_training_panel(self):
        try:
            from AGL_UI.Training_Panel import TrainingPanel
            import tkinter as tk
            win = tk.Toplevel(self)
            win.title('Training Panel')
            panel = TrainingPanel(parent=win, memory_path=None) # type: ignore
            panel.pack(fill='both', expand=True)
            panel.refresh()
        except Exception as e:
            self.output.insert('end', f'Open training panel failed: {e}\n')
