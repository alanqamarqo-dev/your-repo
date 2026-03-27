"""analyze_patent_risks.py
أداة تحليل تلقائي للمخاطر القانونية في الكود (براءات الاختراع)
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json

# مصفوفة المخاطر
RISK_MATRIX = {
    'CLASS_NAMES': {
        'HIGH_RISK': [
            'transformer', 'attention', 'gan', 'vae', 'bert', 'gpt', 'llama',
            'pagerank', 'mapreduce', 'reinforcement', 'qnetwork', 'actorcritic',
            'multiheadattention', 'selfattention', 'crossattention'
        ],
        'MEDIUM_RISK': [
            'encoder', 'decoder', 'embedding', 'neural', 'layer',
            'network', 'model', 'processor', 'autoencoder'
        ],
        'LOW_RISK': [
            'manager', 'controller', 'handler', 'service',
            'helper', 'util', 'tool', 'factory', 'brain', 'engine'
        ]
    },
    'FUNCTION_NAMES': {
        'HIGH_RISK': [
            'attention', 'self_attention', 'transformer_forward',
            'generator_forward', 'discriminator_forward',
            'q_learning', 'policy_gradient', 'scaled_dot_product'
        ],
        'MEDIUM_RISK': [
            'encode', 'decode', 'embed', 'forward', 'backward',
            'train_step', 'predict', 'infer'
        ]
    },
    'INHERITANCE': {
        'HIGH_RISK': [
            'nn.transformer', 'nn.multiheadattention',
            'torch.nn.transformer', 'tf.keras.layers.attention',
            'transformers.', 'huggingface'
        ]
    }
}


class PatentRiskAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.results = []
        
    def analyze_all(self, target_dirs: List[str] = None) -> Dict:
        """تحليل جميع الملفات في المجلدات المستهدفة"""
        if target_dirs is None:
            target_dirs = ['Core_Engines', 'Integration_Layer', 'Scientific_Systems', 'Self_Improvement']
        
        all_results = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'safe': [],
            'summary': {}
        }
        
        for target_dir in target_dirs:
            dir_path = self.root_dir / target_dir
            if not dir_path.exists():
                continue
            
            for py_file in dir_path.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                    
                try:
                    analysis = self.analyze_file(str(py_file))
                    self.results.append(analysis)
                    
                    # تصنيف النتائج
                    risk_level = self._get_overall_risk(analysis)
                    if risk_level == 'HIGH':
                        all_results['high_risk'].append(analysis)
                    elif risk_level == 'MEDIUM':
                        all_results['medium_risk'].append(analysis)
                    elif risk_level == 'LOW':
                        all_results['low_risk'].append(analysis)
                    else:
                        all_results['safe'].append(analysis)
                        
                except Exception as e:
                    print(f"⚠️ فشل تحليل {py_file}: {e}")
        
        # إحصائيات
        all_results['summary'] = {
            'total_files': len(self.results),
            'high_risk_count': len(all_results['high_risk']),
            'medium_risk_count': len(all_results['medium_risk']),
            'low_risk_count': len(all_results['low_risk']),
            'safe_count': len(all_results['safe'])
        }
        
        return all_results
    
    def analyze_file(self, filepath: str) -> Dict:
        """تحليل ملف واحد"""
        result = {
            'file': str(Path(filepath).relative_to(self.root_dir)),
            'classes': [],
            'functions': [],
            'high_risk_items': [],
            'medium_risk_items': [],
            'safe_items': []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # تحليل AST
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_info = self._analyze_class(node, content)
                        result['classes'].append(class_info)
                        
                        risk = self._check_risk(class_info['name'], 'CLASS')
                        if risk['level'] == 'HIGH':
                            result['high_risk_items'].append({
                                'type': 'CLASS',
                                'name': class_info['name'],
                                'reason': risk['reason'],
                                'line': node.lineno
                            })
                        elif risk['level'] == 'MEDIUM':
                            result['medium_risk_items'].append({
                                'type': 'CLASS',
                                'name': class_info['name'],
                                'reason': risk['reason'],
                                'line': node.lineno
                            })
                        else:
                            result['safe_items'].append(f"Class: {class_info['name']}")
                    
                    elif isinstance(node, ast.FunctionDef):
                        if not self._is_method(node):
                            func_name = node.name
                            risk = self._check_risk(func_name, 'FUNCTION')
                            if risk['level'] in ['HIGH', 'MEDIUM']:
                                result[f"{risk['level'].lower()}_risk_items"].append({
                                    'type': 'FUNCTION',
                                    'name': func_name,
                                    'reason': risk['reason'],
                                    'line': node.lineno
                                })
                            
            except SyntaxError:
                result['error'] = 'Syntax error in file'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_class(self, class_node, content: str) -> Dict:
        """تحليل كلاس"""
        class_info = {
            'name': class_node.name,
            'inherits': [],
            'line': class_node.lineno
        }
        
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                class_info['inherits'].append(base.id)
            elif isinstance(base, ast.Attribute):
                class_info['inherits'].append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)
        
        return class_info
    
    def _is_method(self, node) -> bool:
        """تحقق إذا كانت الدالة method داخل كلاس"""
        return hasattr(node, 'col_offset') and node.col_offset > 0
    
    def _check_risk(self, name: str, item_type: str) -> Dict:
        """فحص مستوى الخطورة"""
        name_lower = name.lower()
        
        if item_type == 'CLASS':
            # فحص HIGH RISK
            for risk_pattern in RISK_MATRIX['CLASS_NAMES']['HIGH_RISK']:
                if risk_pattern in name_lower:
                    return {
                        'level': 'HIGH',
                        'reason': f'الاسم يحتوي على "{risk_pattern}" - قد يكون محمياً ببراءة اختراع'
                    }
            
            # فحص MEDIUM RISK
            for risk_pattern in RISK_MATRIX['CLASS_NAMES']['MEDIUM_RISK']:
                if risk_pattern in name_lower:
                    return {
                        'level': 'MEDIUM',
                        'reason': f'الاسم يحتوي على "{risk_pattern}" - يحتاج مراجعة'
                    }
            
            # فحص LOW RISK
            for safe_pattern in RISK_MATRIX['CLASS_NAMES']['LOW_RISK']:
                if safe_pattern in name_lower:
                    return {'level': 'LOW', 'reason': 'اسم عام آمن'}
        
        elif item_type == 'FUNCTION':
            for risk_pattern in RISK_MATRIX['FUNCTION_NAMES']['HIGH_RISK']:
                if risk_pattern in name_lower:
                    return {
                        'level': 'HIGH',
                        'reason': f'اسم الدالة "{risk_pattern}" قد يشير لخوارزمية محمية'
                    }
            
            for risk_pattern in RISK_MATRIX['FUNCTION_NAMES']['MEDIUM_RISK']:
                if risk_pattern in name_lower:
                    return {
                        'level': 'MEDIUM',
                        'reason': f'اسم الدالة "{risk_pattern}" شائع لكن يحتاج توثيق'
                    }
        
        return {'level': 'SAFE', 'reason': 'آمن'}
    
    def _get_overall_risk(self, analysis: Dict) -> str:
        """تحديد مستوى الخطر الإجمالي للملف"""
        if analysis.get('high_risk_items'):
            return 'HIGH'
        elif analysis.get('medium_risk_items'):
            return 'MEDIUM'
        elif analysis.get('low_risk_items'):
            return 'LOW'
        return 'SAFE'
    
    def generate_report(self, results: Dict) -> str:
        """توليد تقرير مفصل"""
        lines = []
        lines.append("=" * 80)
        lines.append("📊 تقرير تحليل المخاطر القانونية (براءات الاختراع)")
        lines.append("=" * 80)
        lines.append("")
        
        summary = results['summary']
        lines.append("📈 الإحصائيات الإجمالية:")
        lines.append(f"   • إجمالي الملفات المحللة: {summary['total_files']}")
        lines.append(f"   🚨 ملفات عالية الخطورة: {summary['high_risk_count']}")
        lines.append(f"   ⚠️  ملفات متوسطة الخطورة: {summary['medium_risk_count']}")
        lines.append(f"   ℹ️  ملفات منخفضة الخطورة: {summary['low_risk_count']}")
        lines.append(f"   ✅ ملفات آمنة: {summary['safe_count']}")
        lines.append("")
        
        if results['high_risk']:
            lines.append("🚨 العناصر عالية الخطورة (تحتاج إجراء فوري):")
            lines.append("-" * 80)
            for file_analysis in results['high_risk'][:10]:  # أول 10
                lines.append(f"\n📁 {file_analysis['file']}")
                for item in file_analysis['high_risk_items']:
                    lines.append(f"   ⚠️  {item['type']}: {item['name']} (سطر {item['line']})")
                    lines.append(f"      السبب: {item['reason']}")
                    lines.append(f"      الإجراء المقترح: إعادة تسمية أو إعادة كتابة")
        
        if results['medium_risk']:
            lines.append("\n⚠️  العناصر متوسطة الخطورة (تحتاج مراجعة):")
            lines.append("-" * 80)
            for file_analysis in results['medium_risk'][:10]:
                lines.append(f"\n📁 {file_analysis['file']}")
                for item in file_analysis['medium_risk_items']:
                    lines.append(f"   • {item['type']}: {item['name']} (سطر {item['line']})")
                    lines.append(f"      السبب: {item['reason']}")
                    lines.append(f"      الإجراء المقترح: إضافة توثيق مرجعي")
        
        lines.append("\n" + "=" * 80)
        lines.append("✅ التوصيات:")
        lines.append("1. إعادة تسمية العناصر عالية الخطورة")
        lines.append("2. إضافة توثيق أكاديمي للعناصر متوسطة الخطورة")
        lines.append("3. مراجعة الوراثة من مكتبات خارجية")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    repo_root = Path(__file__).resolve().parents[1] / "repo-copy"
    if not repo_root.exists():
        repo_root = Path(__file__).resolve().parents[1]
    
    print(f"🔍 بدء التحليل من: {repo_root}")
    
    analyzer = PatentRiskAnalyzer(str(repo_root))
    results = analyzer.analyze_all()
    
    # طباعة التقرير
    report = analyzer.generate_report(results)
    print(report)
    
    # حفظ التفاصيل JSON
    output_dir = Path(__file__).resolve().parents[1] / "artifacts"
    output_dir.mkdir(exist_ok=True)
    
    json_path = output_dir / "patent_risk_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # حفظ التقرير النصي
    report_path = output_dir / "patent_risk_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 تم حفظ النتائج:")
    print(f"   JSON: {json_path}")
    print(f"   تقرير: {report_path}")


if __name__ == '__main__':
    main()
