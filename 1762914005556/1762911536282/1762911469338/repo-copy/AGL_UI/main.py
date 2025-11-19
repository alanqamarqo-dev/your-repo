"""AGL UI - simple local Tkinter GUI launcher

Run: python AGL_UI/main.py
"""
from __future__ import annotations

import tkinter as tk
from ui.dashboard import Dashboard


def main():
    root = tk.Tk()
    root.title("AGL Local UI")
    root.geometry('900x600')
    app = Dashboard(root)
    app.pack(fill='both', expand=True)
    root.mainloop()


if __name__ == '__main__':
    main()
