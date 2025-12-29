import os
import time
import ast

# الكلمات المفتاحية التي تدل على قوة الكود في مشروعك
POWER_KEYWORDS = [
    "Heikal", "Quantum", "Resonance", "Holographic", "Vectorized", 
    "Consciousness", "SelfModel", "Parallel", "Ollama", "UnifiedAGI",
    "Physics", "Wave", "Entanglement"
]

def analyze_file_strength(filepath):
    """تحليل قوة الملف بناءً على المحتوى والتعقيد"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 1. نقاط الكلمات المفتاحية (كل كلمة تزيد القوة)
        keyword_score = sum(content.count(kw) for kw in POWER_KEYWORDS)
        
        # 2. التحليل الهيكلي (عدد الكلاسات والدوال)
        try:
            tree = ast.parse(content)
            classes = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            functions = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            structure_score = (classes * 5) + (functions * 2)
        except:
            structure_score = 0 # إذا كان الكود فيه أخطاء ولا يمكن قراءته
            
        # 3. نقاط الحداثة (الملفات الأحدث تأخذ نقاطاً أكثر قليلاً)
        last_modified = os.path.getmtime(filepath)
        days_old = (time.time() - last_modified) / (60 * 60 * 24)
        recency_score = max(0, 100 - days_old) / 10 # 10 نقاط كحد أقصى للحداثة
        
        # المجموع النهائي
        total_strength = keyword_score + structure_score + recency_score
        
        return {
            "score": int(total_strength),
            "keywords": keyword_score,
            "structure": structure_score,
            "modified": time.ctime(last_modified)
        }
    except Exception as e:
        return {"score": 0, "error": str(e)}

def scan_project():
    print("🔬 [AGL Strength Scanner] Starting Analysis...\n")
    
    files_data = []
    
    for root, dirs, files in os.walk("."):
        if "_TRASH" in root or ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                stats = analyze_file_strength(path)
                files_data.append((file, path, stats))

    # ترتيب الملفات من الأقوى إلى الأضعف
    files_data.sort(key=lambda x: x[2].get('score', 0), reverse=True)

    print(f"{'SCORE':<8} | {'FILE NAME':<40} | {'TYPE'}")
    print("-" * 70)
    
    strong_count = 0
    weak_count = 0
    
    for name, path, stats in files_data:
        score = stats.get('score', 0)
        
        # تصنيف بصري
        if score > 50:
            category = "💎 CORE (Strong)"
            strong_count += 1
        elif score > 10:
            category = "⚙️  Utility"
        else:
            category = "📝 Draft/Weak"
            weak_count += 1
            
        print(f"{score:<8} | {name:<40} | {category}")

    print("\n" + "="*50)
    print(f"📊 Summary:")
    print(f"   - Total Python Files: {len(files_data)}")
    print(f"   - Strong Core Files: {strong_count} (Do NOT Delete)")
    print(f"   - Potential Weak/Old Files: {weak_count} (Review needed)")
    print("="*50)

if __name__ == "__main__":
    scan_project()
