"""Training panel: small UI to show temporal summaries and a simple RMSE over time plot."""
try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    tk = None

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    plt = None

from Learning_System.TemporalMemory import TemporalMemory


class TrainingPanel:
    def __init__(self, parent=None, memory_path: str = None): # type: ignore
        # TemporalMemory may not accept a path arg; be defensive
        try:
            self.tm = TemporalMemory(path=memory_path) # type: ignore
        except Exception:
            try:
                self.tm = TemporalMemory() # type: ignore
            except Exception:
                self.tm = None
        self.parent = parent
        if tk and parent is not None:
            self.frame = ttk.Frame(parent) # type: ignore
            self.summary_label = ttk.Label(self.frame, text='No data') # type: ignore
            self.summary_label.pack()
            self.plot_area = None

    def summary(self, seconds):
        raise NotImplementedError

            btn = ttk.Button(self.frame, text='Refresh', command=self.refresh) # type: ignore
            btn.pack()

    def refresh(self):
        if not self.tm:
            return
        # run non-blocking by deferring heavy plotting
        try:
            s = self.tm.summary(3600) # type: ignore
        except Exception:
            s = {}
        if hasattr(self, 'summary_label'):
            self.summary_label.config(text=str(s))
        # if matplotlib available draw simple timeseries
        if plt:
            xs = []
            ys = []
            for e in self.tm.recent(24 * 3600): # type: ignore
                xs.append(e.get('ts'))
                ys.append(e.get('fit', {}).get('rmse'))
            if xs and ys:
                fig = plt.Figure(figsize=(5, 3)) # type: ignore
                ax = fig.add_subplot(111)
                ax.plot(xs, ys, '-o')
                ax.set_title('RMSE over time')
                ax.set_xlabel('ts')
                ax.set_ylabel('rmse')
                if hasattr(self, 'plot_area') and self.plot_area:
                    self.plot_area.get_tk_widget().destroy()
                self.plot_area = FigureCanvasTkAgg(fig, master=self.frame) # type: ignore
                self.plot_area.draw()
                self.plot_area.get_tk_widget().pack()

    def pack(self, **kwargs):
        if tk and hasattr(self, 'frame'):
            self.frame.pack(**kwargs)
