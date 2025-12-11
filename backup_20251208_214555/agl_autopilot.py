#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AGL Autopilot - الطيار الآلي
المطور: حسام هيكل
التاريخ: 5 ديسمبر 2025
الوظيفة: تشغيل وإدارة نظام AGL بشكل آلي وآمن
"""

import os
import sys
import time
import subprocess
import webbrowser
import signal
import json
from datetime import datetime
from pathlib import Path
import threading
import platform

# =====================================================
# الإعدادات الأساسية
# =====================================================
REPO_PATH = Path(__file__).parent.absolute()
SERVER_SCRIPT = REPO_PATH / "server_fixed.py"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BROWSER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# الملفات المحمية (Read-Only في وضع الإنتاج)
PROTECTED_FILES = [
    "Core_Engines/__init__.py",
    "dynamic_modules/mission_control_enhanced.py",
    "server_fixed.py",
    "Scientific_Systems/Automated_Theorem_Prover.py",
    "Scientific_Systems/Scientific_Research_Assistant.py",
    "Engineering_Engines/Advanced_Code_Generator.py",
    "Self_Improvement/Self_Improvement_Engine.py",
    "Core_Engines/Quantum_Neural_Core.py"
]

# الإعدادات
MONITORING_INTERVAL = 30  # ثانية
AUTO_RESTART = True
PROTECT_FILES = True
AUTO_OPEN_BROWSER = True

# =====================================================
# الألوان للـ Terminal
# =====================================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.END):
    """طباعة ملونة"""
    print(f"{color}{text}{Colors.END}")

def print_header(text):
    """طباعة عنوان"""
    print_colored("=" * 80, Colors.CYAN)
    print_colored(text, Colors.YELLOW)
    print_colored("=" * 80, Colors.CYAN)
    print()

def print_step(step_num, text):
    """طباعة خطوة"""
    print_colored(f"📍 الخطوة {step_num}: {text}", Colors.CYAN)

def print_success(text):
    """طباعة نجاح"""
    print_colored(f"   ✅ {text}", Colors.GREEN)

def print_warning(text):
    """طباعة تحذير"""
    print_colored(f"   ⚠️  {text}", Colors.YELLOW)

def print_error(text):
    """طباعة خطأ"""
    print_colored(f"   ❌ {text}", Colors.RED)

# =====================================================
# كلاس الطيار الآلي
# =====================================================
class AGLAutopilot:
    """الطيار الآلي لنظام AGL"""
    
    def __init__(self):
        self.server_process = None
        self.monitoring = True
        self.start_time = datetime.now()
        self.restart_count = 0
        self.log_file = REPO_PATH / "autopilot.log"
        
    def log(self, message, level="INFO"):
        """كتابة Log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message)
        
        if level == "ERROR":
            print_error(message)
        elif level == "WARNING":
            print_warning(message)
        else:
            print_colored(f"   📝 {message}", Colors.END)
    
    def check_environment(self):
        """التحقق من البيئة"""
        print_step(1, "التحقق من البيئة...")
        
        # التحقق من المسار
        if not REPO_PATH.exists():
            print_error(f"المسار غير موجود: {REPO_PATH}")
            return False
        print_success(f"المسار: {REPO_PATH}")
        
        # التحقق من server_fixed.py
        if not SERVER_SCRIPT.exists():
            print_error(f"السيرفر غير موجود: {SERVER_SCRIPT}")
            return False
        print_success(f"السيرفر: {SERVER_SCRIPT}")
        
        # التحقق من Python
        python_version = sys.version.split()[0]
        print_success(f"Python: {python_version}")
        
        # التحقق من المحركات
        try:
            sys.path.insert(0, str(REPO_PATH))
            from Core_Engines import ENGINE_REGISTRY
            engine_count = len(ENGINE_REGISTRY)
            print_success(f"المحركات: {engine_count} محرك محمل")
        except Exception as e:
            print_warning(f"تحذير: لم يتم تحميل المحركات - {e}")
        
        print()
        return True
    
    def protect_files(self):
        """حماية الملفات الأساسية"""
        if not PROTECT_FILES:
            return
        
        print_step(2, "حماية الملفات الأساسية...")
        
        protected_count = 0
        for file_path in PROTECTED_FILES:
            full_path = REPO_PATH / file_path
            if full_path.exists():
                try:
                    # جعل الملف Read-Only
                    if platform.system() == "Windows":
                        os.system(f'attrib +R "{full_path}"')
                    else:
                        os.chmod(full_path, 0o444)
                    
                    protected_count += 1
                    self.log(f"Protected: {file_path}")
                except Exception as e:
                    print_warning(f"لم يتم حماية {file_path}: {e}")
        
        print_success(f"تم حماية {protected_count} ملف")
        print()
    
    def unprotect_files(self):
        """إلغاء حماية الملفات (عند الإيقاف)"""
        if not PROTECT_FILES:
            return
        
        for file_path in PROTECTED_FILES:
            full_path = REPO_PATH / file_path
            if full_path.exists():
                try:
                    if platform.system() == "Windows":
                        os.system(f'attrib -R "{full_path}"')
                    else:
                        os.chmod(full_path, 0o644)
                except:
                    pass
    
    def start_server(self):
        """تشغيل السيرفر"""
        print_step(3, "تشغيل السيرفر...")
        
        try:
            # تعيين متغيرات البيئة
            env = os.environ.copy()
            env["AGL_ALLOW_EXTERNAL_LLM"] = "true"
            env["PYTHONPATH"] = str(REPO_PATH)
            
            # تشغيل السيرفر
            self.server_process = subprocess.Popen(
                [sys.executable, str(SERVER_SCRIPT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(REPO_PATH)
            )
            
            # انتظار قليلاً للتأكد من التشغيل
            time.sleep(3)
            
            if self.server_process.poll() is None:
                print_success("السيرفر يعمل")
                print_success(f"PID: {self.server_process.pid}")
                print_success(f"URL: {BROWSER_URL}")
                self.log(f"Server started with PID {self.server_process.pid}")
                return True
            else:
                print_error("فشل تشغيل السيرفر")
                return False
        
        except Exception as e:
            print_error(f"خطأ في التشغيل: {e}")
            self.log(f"Failed to start server: {e}", "ERROR")
            return False
        
        finally:
            print()
    
    def open_browser(self):
        """فتح المتصفح"""
        if not AUTO_OPEN_BROWSER:
            return
        
        print_step(4, "فتح المتصفح...")
        
        try:
            # انتظار أطول للتأكد من جاهزية السيرفر
            print_colored("   ⏳ انتظار جاهزية السيرفر...", Colors.YELLOW)
            time.sleep(5)
            
            # محاولة فتح المتصفح بطرق متعددة (Windows)
            browser_opened = False
            
            # الطريقة 1: webbrowser.open مع new=2 (tab جديد)
            try:
                webbrowser.open(BROWSER_URL, new=2)
                browser_opened = True
                print_success(f"تم فتح المتصفح: {BROWSER_URL}")
            except Exception as e1:
                print_warning(f"الطريقة 1 فشلت: {e1}")
                
                # الطريقة 2: استخدام start على Windows
                if platform.system() == "Windows":
                    try:
                        subprocess.Popen(['cmd', '/c', 'start', BROWSER_URL], 
                                       shell=True,
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        browser_opened = True
                        print_success(f"تم فتح المتصفح (cmd): {BROWSER_URL}")
                    except Exception as e2:
                        print_warning(f"الطريقة 2 فشلت: {e2}")
            
            if browser_opened:
                self.log("Browser opened successfully")
            else:
                print_warning("لم يتم فتح المتصفح تلقائياً")
                print_colored(f"\n   🌐 افتح المتصفح يدوياً: {BROWSER_URL}\n", Colors.CYAN)
                
        except Exception as e:
            print_warning(f"خطأ في فتح المتصفح: {e}")
            print_colored(f"\n   🌐 افتح المتصفح يدوياً: {BROWSER_URL}\n", Colors.CYAN)
        
        print()
    
    def check_server_health(self):
        """التحقق من صحة السيرفر"""
        if self.server_process is None:
            return False
        
        return self.server_process.poll() is None
    
    def restart_server(self):
        """إعادة تشغيل السيرفر"""
        print_warning("إعادة تشغيل السيرفر...")
        self.log("Restarting server", "WARNING")
        
        # إيقاف السيرفر القديم
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
        
        # تشغيل جديد
        self.restart_count += 1
        return self.start_server()
    
    def monitor_system(self):
        """مراقبة النظام"""
        print_step(5, "بدء المراقبة المستمرة...")
        print_success(f"التحقق كل {MONITORING_INTERVAL} ثانية")
        print_success(f"إعادة التشغيل التلقائي: {'مفعّل' if AUTO_RESTART else 'معطّل'}")
        print()
        
        print_colored("━" * 80, Colors.CYAN)
        print_colored("🤖 الطيار الآلي نشط - النظام تحت المراقبة", Colors.GREEN)
        print_colored("━" * 80, Colors.CYAN)
        print()
        
        while self.monitoring:
            time.sleep(MONITORING_INTERVAL)
            
            # التحقق من صحة السيرفر
            if not self.check_server_health():
                print_error("السيرفر متوقف!")
                self.log("Server stopped unexpectedly", "ERROR")
                
                if AUTO_RESTART:
                    if self.restart_server():
                        print_success("تم إعادة التشغيل بنجاح")
                    else:
                        print_error("فشلت إعادة التشغيل")
                        self.log("Failed to restart server", "ERROR")
                        break
                else:
                    break
            else:
                # تقرير دوري
                uptime = datetime.now() - self.start_time
                uptime_str = str(uptime).split('.')[0]
                
                print_colored(f"💚 النظام يعمل | Uptime: {uptime_str} | إعادات: {self.restart_count}", Colors.GREEN)
                self.log(f"System healthy - Uptime: {uptime_str}, Restarts: {self.restart_count}")
    
    def stop(self):
        """إيقاف الطيار الآلي"""
        print()
        print_colored("━" * 80, Colors.CYAN)
        print_colored("⏹️  إيقاف الطيار الآلي...", Colors.YELLOW)
        print_colored("━" * 80, Colors.CYAN)
        print()
        
        self.monitoring = False
        
        # إيقاف السيرفر
        if self.server_process:
            print("   🛑 إيقاف السيرفر...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print_success("السيرفر متوقف")
            except:
                try:
                    self.server_process.kill()
                    print_success("السيرفر متوقف (Force)")
                except:
                    print_warning("لم يتم إيقاف السيرفر")
        
        # إلغاء حماية الملفات
        print("   🔓 إلغاء حماية الملفات...")
        self.unprotect_files()
        print_success("تم إلغاء الحماية")
        
        # تقرير نهائي
        uptime = datetime.now() - self.start_time
        print()
        print_colored("📊 الإحصائيات:", Colors.YELLOW)
        print(f"   ⏱️  وقت التشغيل: {uptime}")
        print(f"   🔄 إعادات التشغيل: {self.restart_count}")
        print(f"   📝 سجل الأحداث: {self.log_file}")
        print()
        
        self.log("Autopilot stopped")
        print_colored("✅ تم الإيقاف بنجاح", Colors.GREEN)
    
    def run(self):
        """تشغيل الطيار الآلي"""
        print_header("🤖 AGL Autopilot - الطيار الآلي")
        print_colored("   المطور: حسام هيكل | التاريخ: 5 ديسمبر 2025", Colors.END)
        print_colored("   الوظيفة: تشغيل وإدارة نظام AGL بشكل آلي وآمن", Colors.END)
        print()
        
        self.log("Autopilot starting...")
        
        try:
            # 1. التحقق من البيئة
            if not self.check_environment():
                print_error("فشل التحقق من البيئة")
                return False
            
            # 2. حماية الملفات
            self.protect_files()
            
            # 3. تشغيل السيرفر
            if not self.start_server():
                print_error("فشل تشغيل السيرفر")
                return False
            
            # 4. فتح المتصفح
            self.open_browser()
            
            # 5. بدء المراقبة
            self.monitor_system()
            
            return True
        
        except KeyboardInterrupt:
            print()
            print_warning("تم الإيقاف بواسطة المستخدم (Ctrl+C)")
            return True
        
        except Exception as e:
            print_error(f"خطأ غير متوقع: {e}")
            self.log(f"Unexpected error: {e}", "ERROR")
            return False
        
        finally:
            self.stop()

# =====================================================
# معالج الإشارات (Signal Handler)
# =====================================================
autopilot_instance = None

def signal_handler(sig, frame):
    """معالج إشارة الإيقاف"""
    if autopilot_instance:
        autopilot_instance.monitoring = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# =====================================================
# نقطة الدخول الرئيسية
# =====================================================
def main():
    """نقطة الدخول الرئيسية"""
    global autopilot_instance
    
    # تعيين مسار العمل
    os.chdir(REPO_PATH)
    
    # إنشاء وتشغيل الطيار الآلي
    autopilot_instance = AGLAutopilot()
    success = autopilot_instance.run()
    
    # كود الخروج
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

# EOF
