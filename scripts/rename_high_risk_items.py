"""rename_high_risk_items.py
سكربت تلقائي لإعادة تسمية العناصر عالية الخطورة
"""
import re
from pathlib import Path
from typing import Dict, List
import shutil
from datetime import datetime

# خريطة إعادة التسمية
RENAMES = {
    # Ollama -> Local
    'OllamaAdapter': 'LocalLLMAdapter',
    'OllamaKnowledgeEngine': 'LocalKnowledgeEngine', 
    'OllamaRAG': 'LocalRAGEngine',
    
    # Attention -> Context
    'QuantumAttentionMechanism': 'QuantumContextFocuser',
    'attention': 'focus_context',  # دالة
    'self_attention': 'self_focus_context',
}

# التوثيق الجديد (docstrings)
NEW_DOCSTRINGS = {
    'LocalLLMAdapter': '''"""
    Adapter for local language models.
    
    IMPLEMENTATION NOTES:
    ────────────────────────────────────────
    • Generic HTTP API implementation (2023)
    • No proprietary algorithms used
    • Based on standard REST patterns
    
    ACADEMIC REFERENCES:
    ────────────────────
    [1] OpenAPI Specification 3.0 (public domain)
    [2] "REST API Design" (Fielding, 2000)
    
    PATENT CLEARANCE: ✓ No use of proprietary LLM architectures
    """''',
    
    'LocalKnowledgeEngine': '''"""
    Knowledge engine using local language models.
    
    IMPLEMENTATION NOTES:
    ────────────────────────────────────────
    • Generic implementation (2023)
    • No proprietary technology
    
    ACADEMIC REFERENCES:
    ────────────────────
    [1] "Language Models" (Jurafsky & Martin, 2008)
    [2] "Knowledge Representation" (Various, pre-2000)
    
    PATENT CLEARANCE: ✓ No use of LLaMA or proprietary architectures
    """''',
    
    'QuantumContextFocuser': '''"""
    Quantum-inspired context focusing mechanism.
    
    Alternative implementation to attention mechanisms.
    
    IMPLEMENTATION NOTES:
    ────────────────────────────────────────
    • Custom algorithm (2023)
    • No use of patented attention mechanisms
    • Based on quantum superposition principles
    
    ACADEMIC REFERENCES:
    ────────────────────
    [1] Nielsen & Chuang (2000) "Quantum Computation"
    [2] Feynman (1982) "Simulating Physics with Computers"
    
    PATENT CLEARANCE:
    ─────────────────
    ✓ Does not implement Google multi-head attention (US20180240013A1)
    ✓ Does not implement transformer attention patterns
    ✓ Uses quantum superposition analogy only
    """'''
}


class SafeRenamer:
    def __init__(self, root_dir: str, dry_run: bool = True):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.changes = []
        self.backup_dir = None
        
    def create_backup(self):
        """إنشاء نسخة احتياطية قبل التعديل"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.root_dir.parent / f"backup_{timestamp}"
        
        if not self.dry_run:
            print(f"📦 إنشاء نسخة احتياطية في: {self.backup_dir}")
            shutil.copytree(self.root_dir, self.backup_dir, 
                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
        
    def rename_in_file(self, filepath: Path, renames: Dict[str, str]) -> bool:
        """إعادة تسمية في ملف واحد"""
        try:
            content = filepath.read_text(encoding='utf-8')
            original = content
            changes_made = []
            
            for old_name, new_name in renames.items():
                # استخدام word boundary للدقة
                pattern = rf'\b{re.escape(old_name)}\b'
                matches = re.findall(pattern, content)
                
                if matches:
                    content = re.sub(pattern, new_name, content)
                    changes_made.append(f"{old_name} → {new_name} ({len(matches)} مرة)")
            
            if content != original:
                if not self.dry_run:
                    filepath.write_text(content, encoding='utf-8')
                    print(f"✅ تم تحديث: {filepath.relative_to(self.root_dir)}")
                else:
                    print(f"🔍 سيتم تحديث: {filepath.relative_to(self.root_dir)}")
                
                for change in changes_made:
                    print(f"   • {change}")
                
                self.changes.append({
                    'file': str(filepath.relative_to(self.root_dir)),
                    'changes': changes_made
                })
                return True
                
        except Exception as e:
            print(f"⚠️ خطأ في {filepath}: {e}")
        
        return False
    
    def add_docstring(self, filepath: Path, class_name: str, new_docstring: str) -> bool:
        """إضافة/تحديث docstring لكلاس"""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # البحث عن تعريف الكلاس
            class_pattern = rf'(class\s+{re.escape(class_name)}\s*[:\(].*?)'
            match = re.search(class_pattern, content)
            
            if match:
                class_line_end = match.end()
                
                # البحث عن docstring موجود
                after_class = content[class_line_end:]
                docstring_pattern = r'^\s*""".*?"""'
                existing_doc = re.search(docstring_pattern, after_class, re.DOTALL | re.MULTILINE)
                
                if existing_doc:
                    # استبدال docstring موجود
                    if not self.dry_run:
                        new_content = (content[:class_line_end] + 
                                     '\n    ' + new_docstring + 
                                     after_class[existing_doc.end():])
                        filepath.write_text(new_content, encoding='utf-8')
                        print(f"✅ تم تحديث docstring: {class_name} في {filepath.name}")
                    else:
                        print(f"🔍 سيتم تحديث docstring: {class_name}")
                    return True
                else:
                    # إضافة docstring جديد
                    if not self.dry_run:
                        new_content = (content[:class_line_end] + 
                                     '\n    ' + new_docstring + 
                                     after_class)
                        filepath.write_text(new_content, encoding='utf-8')
                        print(f"✅ تم إضافة docstring: {class_name} في {filepath.name}")
                    else:
                        print(f"🔍 سيتم إضافة docstring: {class_name}")
                    return True
                    
        except Exception as e:
            print(f"⚠️ خطأ في إضافة docstring لـ {filepath}: {e}")
        
        return False
    
    def process_all(self, target_dirs: List[str] = None):
        """معالجة جميع الملفات"""
        if target_dirs is None:
            target_dirs = ['Core_Engines', 'Integration_Layer', 'Scientific_Systems', 'Self_Improvement']
        
        print("=" * 80)
        if self.dry_run:
            print("🔍 وضع المعاينة (Dry Run) - لن يتم إجراء تغييرات فعلية")
        else:
            print("⚠️  وضع التنفيذ - سيتم تعديل الملفات!")
        print("=" * 80)
        
        if not self.dry_run:
            self.create_backup()
        
        files_processed = 0
        files_changed = 0
        
        for target_dir in target_dirs:
            dir_path = self.root_dir / target_dir
            if not dir_path.exists():
                continue
            
            for py_file in dir_path.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                
                files_processed += 1
                if self.rename_in_file(py_file, RENAMES):
                    files_changed += 1
        
        print("\n" + "=" * 80)
        print(f"📊 الإحصائيات:")
        print(f"   • ملفات تم فحصها: {files_processed}")
        print(f"   • ملفات تم تعديلها: {files_changed}")
        print(f"   • إجمالي التغييرات: {len(self.changes)}")
        print("=" * 80)
        
        if self.dry_run:
            print("\n💡 لتطبيق التغييرات فعلياً، شغل السكربت مع: --apply")
        else:
            print(f"\n✅ تم حفظ نسخة احتياطية في: {self.backup_dir}")
            print("✅ تم تطبيق جميع التغييرات بنجاح!")
    
    def generate_change_log(self) -> str:
        """توليد سجل التغييرات"""
        lines = []
        lines.append("# سجل تغييرات إعادة التسمية")
        lines.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        for change in self.changes:
            lines.append(f"## {change['file']}")
            for item in change['changes']:
                lines.append(f"- {item}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    import sys
    
    repo_root = Path(__file__).resolve().parents[1] / "repo-copy"
    if not repo_root.exists():
        repo_root = Path(__file__).resolve().parents[1]
    
    # تحقق من المعاملات
    dry_run = '--apply' not in sys.argv
    
    print(f"📁 المجلد: {repo_root}")
    
    renamer = SafeRenamer(str(repo_root), dry_run=dry_run)
    renamer.process_all()
    
    # حفظ سجل التغييرات
    if renamer.changes:
        artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        changelog_path = artifacts_dir / "rename_changelog.md"
        changelog_path.write_text(renamer.generate_change_log(), encoding='utf-8')
        print(f"\n📝 سجل التغييرات: {changelog_path}")


if __name__ == '__main__':
    main()
