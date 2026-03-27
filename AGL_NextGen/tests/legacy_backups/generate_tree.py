import os
import ast

ignored_dirs = {'__pycache__', 'backups', 'artifacts', 'repo-copy', 'logs', 'venv', '.git', '.vscode'}

def get_definitions(file_path):
    with open(file_path, "r", encoding="utf-8") as source:
        try:
            tree = ast.parse(source.read())
        except:
            return [], []
    
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")]
    return classes, functions

def translate_to_arabic(name):
    # Simple dictionary for common terms
    translations = {
        "OpticalHeart": "القلب البصري (OpticalHeart)",
        "VectorizedWaveProcessor": "معالج الموجات الموجه (VectorizedWaveProcessor)",
        "ResonanceOptimizer": "محسن الرنين (ResonanceOptimizer)",
        "AGL_Super_Intelligence": "الذكاء الخارق (AGL_Super_Intelligence)",
        "HeikalQuantumCore": "نواة هيكل الكمومية (HeikalQuantumCore)",
        "MoralReasoner": "المفكر الأخلاقي (MoralReasoner)",
        "DreamingEngine": "محرك الأحلام (DreamingEngine)",
        "VolitionEngine": "محرك الإرادة (VolitionEngine)",
        "SelfAwarenessModule": "وحدة الوعي الذاتي (SelfAwarenessModule)",
        "KnowledgeNetwork": "شبكة المعرفة (KnowledgeNetwork)",
        "QuantumNeuralCore": "النواة العصبية الكمومية (QuantumNeuralCore)",
        "CausalGraphEngine": "محرك الرسم البياني السببي (CausalGraphEngine)",
        "SelfLearning": "التعلم الذاتي (SelfLearning)",
        "StrategicThinkingEngine": "محرك التفكير الاستراتيجي (StrategicThinkingEngine)",
        "init": "تهيئة",
        "process_task": "معالجة المهمة",
        "analyze": "تحليل",
        "optimize": "تحسين",
        "get_light_entropy": "الحصول على إنتروبيا الضوء",
        "sync_optical_heart": "مزامنة القلب البصري",
        "set_params_from_entropy": "تعيين المعلمات من الإنتروبيا"
    }
    return translations.get(name, name)

def print_tree(startpath):
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}📂 {os.path.basename(root)}/')
        
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith('.py'):
                print(f'{subindent}📜 {f}')
                classes, functions = get_definitions(os.path.join(root, f))
                
                if classes:
                    print(f'{subindent}    📦 الكلاسات (Classes):')
                    for c in classes:
                        print(f'{subindent}        - {translate_to_arabic(c)}')
                
                if functions:
                    print(f'{subindent}    🔧 الدوال (Functions):')
                    # Limit functions to first 5 to avoid clutter
                    for func in functions[:5]: 
                        print(f'{subindent}        - {translate_to_arabic(func)}')
                    if len(functions) > 5:
                         print(f'{subindent}        - ... (+{len(functions)-5} others)')

if __name__ == "__main__":
    src_path = os.path.join("D:\\AGL\\AGL_NextGen\\src\\agl")
    print(f"Project Tree for: {src_path}\n")
    print_tree(src_path)
