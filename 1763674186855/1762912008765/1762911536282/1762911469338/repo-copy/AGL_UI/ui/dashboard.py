import tkinter as tk
from tkinter import ttk
from .components import RunControls, StatusPanel
from .report_viewer import ReportViewer


class Dashboard(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master # type: ignore
        self._create_widgets()

    def _create_widgets(self):
        self.controls = RunControls(self)
        self.controls.pack(side='top', fill='x', padx=8, pady=8)

        self.status = StatusPanel(self)
        self.status.pack(side='left', fill='y', padx=8, pady=8)

        self.viewer = ReportViewer(self)
        self.viewer.pack(side='right', fill='both', expand=True, padx=8, pady=8)
        # expose attributes for child components
        self.controls.master = self
        self.viewer.master = self
        self.status.master = self
