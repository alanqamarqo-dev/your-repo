import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
import shutil
from tkinter import messagebox


class RunControls(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self._build()

    def _build(self):
        tk.Label(self, text='AGL Controls').pack(side='left', padx=8)
        self.task_var = tk.StringVar(value='حل نظام المعادلات التفاضلية')
        tk.Entry(self, textvariable=self.task_var, width=60).pack(side='left', padx=8)
        tk.Button(self, text='تشغيل المهمة', command=self._on_run).pack(side='left', padx=4)
        tk.Button(self, text='تشغيل كمنظومة (LLM)', command=self._on_run_as_system).pack(side='left', padx=4)
        tk.Button(self, text='عرض السجل', command=self._on_show_logs).pack(side='left', padx=4)
        tk.Button(self, text='السجل الكامل', command=self._on_full_log).pack(side='left', padx=4)

    def _on_run(self):
        task = self.task_var.get()
        if not task or not task.strip():
            messagebox.showwarning('تنبيه', 'الرجاء إدخال وصف المهمة.')
            return
        cmd = [sys.executable, os.path.join(os.getcwd(), 'AGL.py'), '--task', task, '--report', os.path.join('reports', 'last_run.json')]
        try:
            # run synchronously so we can refresh the report immediately
            subprocess.run(cmd, check=True)
            # refresh viewer and status if available
            parent = getattr(self.master, 'viewer', None)
            if parent:
                try:
                    parent.refresh()
                except Exception:
                    pass
            status = getattr(self.master, 'status', None)
            if status:
                status.update_status('Last run completed')
            messagebox.showinfo('نجاح', 'تم تنفيذ المهمة وتحديث التقرير.')
        except Exception as e:
            messagebox.showerror('خطأ', str(e))

    def _on_show_logs(self):
        # delegate to the report viewer which has a log display helper
        viewer = getattr(self.master, 'viewer', None)
        if viewer:
            viewer.show_logs()
        else:
            messagebox.showinfo('معلومات', 'عارض التقارير غير متوفر')

    def _on_run_as_system(self):
        """Run the orchestrated forced-LLM pipeline and update the last_run.json for the UI."""
        # ask for confirmation because this may call external model runtimes and take time
        if not messagebox.askyesno('Confirm', 'هل تريد تشغيل المنظومة كوحدة موحدة (قد يستغرق وقتًا)؟'):
            return

        # prepare environment overrides (use existing env or fallbacks)
        env = os.environ.copy()
        env['AGL_EXTERNAL_INFO_IMPL'] = env.get('AGL_EXTERNAL_INFO_IMPL', 'ollama_adapter')
        env['AGL_OLLAMA_KB_MODEL'] = env.get('AGL_OLLAMA_KB_MODEL', 'qwen2.5:7b-instruct')
        env['AGL_OLLAMA_KB_CACHE_ENABLE'] = '0'

        script_path = os.path.join(os.getcwd(), 'scripts', 'run_agl_orchestrated.py')
        if not os.path.exists(script_path):
            messagebox.showerror('خطأ', f'Script not found: {script_path}')
            return

        try:
            # run synchronously so UI can refresh after completion
            subprocess.run([sys.executable, script_path], check=True, env=env)
        except subprocess.CalledProcessError as e:
            messagebox.showerror('خطأ', f'فشل تشغيل المنظومة: {e}')
            return
        except Exception as e:
            messagebox.showerror('خطأ', str(e))
            return

        # copy forced-LLM output into last_run.json so ReportViewer shows it
        forced = os.path.join('reports', 'agl_orchestrated_response_forced_llm.json')
        target = os.path.join('reports', 'last_run.json')
        try:
            if os.path.exists(forced):
                shutil.copyfile(forced, target)
                # refresh viewer if available
                parent = getattr(self.master, 'viewer', None)
                if parent:
                    try:
                        parent.refresh()
                    except Exception:
                        pass
                status = getattr(self.master, 'status', None)
                if status:
                    status.update_status('Last run (LLM) completed')
                messagebox.showinfo('نجاح', 'تم تشغيل المنظومة وتهيئة التقرير للعرض في الواجهة.')
            else:
                messagebox.showwarning('تنبيه', f'ملف النتيجة لم يُولَّد: {forced}')
        except Exception as e:
            messagebox.showerror('خطأ', f'فشل نسخ النتيجة: {e}')

    def _on_full_log(self):
        viewer = getattr(self.master, 'viewer', None)
        if viewer and hasattr(viewer, '_on_full_log'):
            try:
                viewer._on_full_log()
                return
            except Exception:
                pass
        # fallback: open a simple window ourselves
        log_path = os.path.join(os.getcwd(), 'logs', 'agl.log')
        top = tk.Toplevel(self)
        top.title('السجل الكامل - logs/agl.log')
        text = tk.Text(top, wrap='none')
        text.pack(fill='both', expand=True)
        try:
            if not os.path.exists(log_path):
                text.insert('1.0', 'Log file not found')
                return
            with open(log_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                content = f.read()
            text.insert('1.0', content)
        except Exception as e:
            text.insert('1.0', f'Failed to open log: {e}')


class StatusPanel(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        tk.Label(self, text='الحالة').pack(anchor='nw')
        self.txt = tk.Label(self, text='Idle')
        self.txt.pack(anchor='nw')

    def update_status(self, text: str):
        try:
            self.txt.config(text=str(text))
        except Exception:
            pass
