"""Rollback mechanism: file-backed restore points and validation."""
import os
import shutil
import time
import json

class RollbackMechanism:
    def __init__(self, target_file):
        """
        نظام استعادة يعتمد على الملفات.
        target_file: المسار الكامل للملف المراد حمايته (مثل fusion_weights.json)
        """
        self.target_file = os.path.abspath(target_file)
        self.backup_file = self.target_file + ".bak"
        self.timestamped_backup = None

    def create_restore_point(self):
        """إنشاء نسخة احتياطية على القرص"""
        if os.path.exists(self.target_file):
            try:
                # 1. التحديث السريع (.bak)
                shutil.copy2(self.target_file, self.backup_file)
                
                # 2. الأرشيف الزمني (للطوارئ)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(self.target_file), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                self.timestamped_backup = os.path.join(backup_dir, f"{os.path.basename(self.target_file)}_{timestamp}.bak")
                shutil.copy2(self.target_file, self.timestamped_backup)
                
                print(f">> [Rollback] 🛡️ Restore point secured: {os.path.basename(self.backup_file)}")
                return True
            except Exception as e:
                print(f">> [Rollback] ⚠️ Backup failed: {e}")
                return False
        return False

    def restore(self):
        """استعادة الملف من النسخة الاحتياطية"""
        if os.path.exists(self.backup_file):
            print(f">> [Rollback] 🔄 REVERTING changes to {os.path.basename(self.target_file)}...")
            try:
                shutil.copy2(self.backup_file, self.target_file)
                print(">> [Rollback] ✅ System restored to previous healthy state.")
                return True
            except Exception as e:
                print(f">> [Rollback] ❌ CRITICAL: Restore failed! Error: {e}")
                return False
        else:
            print(">> [Rollback] ❌ No backup file found to restore from!")
            return False

    def validate_fusion_schema(self, new_data: dict) -> bool:
        """التحقق من صحة البيانات قبل المخاطرة بالكتابة"""
        ALLOWED_KEYS = {
            "mathematical_brain", 
            "quantum_processor", 
            "code_generator", 
            "protocol_designer"
        }
        try:
            # 1. فحص المفاتيح الدخيلة
            for key in new_data.keys():
                if key not in ALLOWED_KEYS:
                    print(f">> [Validation] ❌ Unknown neural key: {key}")
                    return False
            
            # 2. فحص سلامة الأرقام
            for key, value in new_data.items():
                if not isinstance(value, (int, float)):
                    print(f">> [Validation] ❌ Non-numeric weight for {key}")
                    return False
                if not (0.0 <= value <= 2.0): # نسمح بزيادة طفيفة حتى 2.0
                    print(f">> [Validation] ❌ Weight out of safe bounds (0-2): {value}")
                    return False
            
            print(">> [Validation] ✅ Neural Schema Validated.")
            return True
        except Exception as e:
            print(f">> [Validation] Error: {e}")
            return False

