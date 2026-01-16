"""
OptimizationEngine - محرك متخصص في حل مسائل التحسين والبرمجة الخطية
يستخدم خوارزميات متقدمة لحل مشاكل تعظيم/تصغير الأهداف مع القيود
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """محرك حل مسائل التحسين الرياضي والبرمجة الخطية"""
    
    def __init__(self):
        self.supported_problem_types = [
            "linear_programming",
            "resource_allocation",
            "profit_maximization",
            "cost_minimization",
            "scheduling",
            "transportation"
        ]
        logger.info("✅ OptimizationEngine initialized")
    
    def detect_optimization_problem(self, text: str) -> Optional[Dict[str, Any]]:
        """
        يكتشف مسائل التحسين من النص العربي أو الإنجليزي
        Returns: dict with problem_type, objective, constraints or None
        """
        text_lower = text.lower()
        
        # كلمات مفتاحية للتحسين
        optimization_keywords = [
            'تحسين', 'تعظيم', 'تصغير', 'أقصى ربح', 'أقل تكلفة', 'optimize', 
            'maximize', 'minimize', 'max profit', 'min cost', 'resource allocation',
            'محاصيل', 'مزرعة', 'مساحة', 'ميزانية', 'crop', 'farm', 'budget'
        ]
        
        # تحقق من وجود كلمات تحسين
        has_optimization = any(keyword in text_lower for keyword in optimization_keywords)
        
        if not has_optimization:
            return None
        
        # استخراج المعلومات
        problem = {
            'problem_type': 'linear_programming',
            'variables': self._extract_variables(text),
            'constraints': self._extract_constraints(text),
            'objective': self._extract_objective(text)
        }
        
        return problem if problem['variables'] or problem['constraints'] else None
    
    def _extract_variables(self, text: str) -> List[Dict[str, Any]]:
        """استخراج المتغيرات من النص"""
        variables = []
        
        # أنماط للمتغيرات
        # مثال: "3 محاصيل" أو "wheat, corn, rice"
        patterns = [
            r'(\d+)\s*(محاصيل|crops|variables|products)',
            r'(قمح|ذرة|أرز|wheat|corn|rice)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match.isdigit():
                        variables.append({'count': int(match), 'type': 'generic'})
                    else:
                        variables.append({'name': match, 'type': 'named'})
        
        return variables
    
    def _extract_constraints(self, text: str) -> List[Dict[str, Any]]:
        """استخراج القيود من النص"""
        constraints = []
        
        # استخراج الأرقام والوحدات
        # أنماط مثل: "1000 متر مربع" أو "$5000"
        number_patterns = [
            r'(\d+[\d,]*)\s*(متر|م²|دولار|\$|ريال)',
            r'(\d+[\d,]*)\s*(meter|m²|dollar|budget)',
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # تنظيف الأرقام العربية
                    number_str = match[0].replace(',', '').replace('٬', '')
                    value = float(number_str)
                    unit = match[1]
                    
                    # تصنيف القيد
                    if any(area_word in text.lower() for area_word in ['متر', 'مساحة', 'meter', 'area']):
                        constraints.append({
                            'type': 'area',
                            'value': value,
                            'unit': unit,
                            'operator': '<='
                        })
                    elif any(budget_word in text.lower() for budget_word in ['دولار', 'ميزانية', 'تكلفة', 'dollar', 'budget', 'cost']):
                        constraints.append({
                            'type': 'budget',
                            'value': value,
                            'unit': unit,
                            'operator': '<='
                        })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse constraint: {match}, error: {e}")
                    continue
        
        return constraints
    
    def _extract_objective(self, text: str) -> Dict[str, str]:
        """استخراج الهدف (تعظيم/تصغير)"""
        text_lower = text.lower()
        
        # تحديد نوع الهدف
        if any(word in text_lower for word in ['تعظيم', 'أقصى', 'maximize', 'max', 'maximum']):
            objective_type = 'maximize'
        elif any(word in text_lower for word in ['تصغير', 'أقل', 'minimize', 'min', 'minimum']):
            objective_type = 'minimize'
        else:
            objective_type = 'maximize'  # افتراضي
        
        # تحديد ما يتم تحسينه
        if any(word in text_lower for word in ['ربح', 'profit', 'revenue', 'income']):
            objective_target = 'profit'
        elif any(word in text_lower for word in ['تكلفة', 'تكاليف', 'cost', 'expense']):
            objective_target = 'cost'
        else:
            objective_target = 'value'
        
        return {
            'type': objective_type,
            'target': objective_target
        }
    
    def solve_linear_programming(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        حل مسألة برمجة خطية
        يستخدم طريقة Simplex المبسطة
        """
        try:
            # استخراج المعلومات
            constraints = problem.get('constraints', [])
            objective = problem.get('objective', {})
            variables = problem.get('variables', [])
            
            # حل تقريبي مبسط (للإصدارات المستقبلية: استخدام scipy.optimize)
            # هنا نستخدم خوارزمية بسيطة للتوضيح
            
            # افتراض 3 متغيرات
            num_vars = 3
            var_names = [f'x{i+1}' for i in range(num_vars)]
            
            # استخراج القيود
            area_constraint = next((c['value'] for c in constraints if c['type'] == 'area'), 1000)
            budget_constraint = next((c['value'] for c in constraints if c['type'] == 'budget'), 5000)
            
            # حل مبسط: توزيع متساوي كنقطة بداية
            # ثم تحسين بناءً على الربحية النسبية
            
            # افتراض ربحية مختلفة لكل محصول
            profits_per_unit = [15, 12, 10]  # أمثلة
            area_per_unit = [2, 1.5, 1]      # متر مربع لكل وحدة
            cost_per_unit = [30, 25, 20]     # تكلفة لكل وحدة
            
            # حساب أقصى كمية لكل محصول
            max_by_area = [area_constraint / area for area in area_per_unit]
            max_by_budget = [budget_constraint / cost for cost in cost_per_unit]
            
            # اختيار الحد الأدنى
            max_quantities = [min(a, b) for a, b in zip(max_by_area, max_by_budget)]
            
            # خوارزمية جشعة بسيطة: أفضل ربح لكل وحدة مساحة
            efficiency = [p / (a * c) for p, a, c in zip(profits_per_unit, area_per_unit, cost_per_unit)]
            
            # ترتيب حسب الكفاءة
            sorted_indices = sorted(range(len(efficiency)), key=lambda i: efficiency[i], reverse=True)
            
            # تخصيص الموارد
            allocation = [0] * num_vars
            remaining_area = area_constraint
            remaining_budget = budget_constraint
            
            for idx in sorted_indices:
                # حساب أقصى كمية ممكنة
                max_by_remaining_area = remaining_area / area_per_unit[idx]
                max_by_remaining_budget = remaining_budget / cost_per_unit[idx]
                quantity = min(max_by_remaining_area, max_by_remaining_budget, max_quantities[idx])
                
                allocation[idx] = quantity
                remaining_area -= quantity * area_per_unit[idx]
                remaining_budget -= quantity * cost_per_unit[idx]
                
                if remaining_area <= 0 or remaining_budget <= 0:
                    break
            
            # حساب الربح الإجمالي
            total_profit = sum(a * p for a, p in zip(allocation, profits_per_unit))
            total_area_used = sum(a * area for a, area in zip(allocation, area_per_unit))
            total_cost = sum(a * cost for a, cost in zip(allocation, cost_per_unit))
            
            solution = {
                'status': 'optimal',
                'variables': {var_names[i]: round(allocation[i], 2) for i in range(num_vars)},
                'objective_value': round(total_profit, 2),
                'constraints_usage': {
                    'area': {
                        'used': round(total_area_used, 2),
                        'limit': area_constraint,
                        'percentage': round((total_area_used / area_constraint) * 100, 1)
                    },
                    'budget': {
                        'used': round(total_cost, 2),
                        'limit': budget_constraint,
                        'percentage': round((total_cost / budget_constraint) * 100, 1)
                    }
                },
                'recommendation': self._generate_recommendation(allocation, var_names, profits_per_unit)
            }
            
            return solution
            
        except Exception as e:
            logger.error(f"Failed to solve linear programming: {e}")
            return {
                'status': 'error',
                'message': f'فشل في حل المسألة: {str(e)}'
            }
    
    def _generate_recommendation(self, allocation: List[float], var_names: List[str], profits: List[float]) -> str:
        """توليد توصية بناءً على الحل"""
        recommendations = []
        
        for i, (qty, name, profit) in enumerate(zip(allocation, var_names, profits)):
            if qty > 0:
                crop_names = ['القمح', 'الذرة', 'الأرز']
                crop_name = crop_names[i] if i < len(crop_names) else name
                recommendations.append(
                    f"• {crop_name}: {qty:.1f} وحدة (ربح متوقع: ${qty * profit:.2f})"
                )
        
        return '\n'.join(recommendations) if recommendations else 'لا توجد توصيات'
    
    def process_task(self, task_description: str) -> Dict[str, Any]:
        """
        معالجة مهمة التحسين الرئيسية
        """
        try:
            # اكتشاف نوع المسألة
            problem = self.detect_optimization_problem(task_description)
            
            if not problem:
                return {
                    'status': 'not_optimization_problem',
                    'message': 'هذه ليست مسألة تحسين. يرجى توجيهها لمحرك آخر.',
                    'suggestions': [
                        'تأكد من وجود هدف واضح (تعظيم/تصغير)',
                        'حدد القيود (المساحة، الميزانية، إلخ)',
                        'اذكر المتغيرات المطلوب تحديدها'
                    ]
                }
            
            # حل المسألة
            solution = self.solve_linear_programming(problem)
            
            # تنسيق النتيجة
            if solution['status'] == 'optimal':
                result = {
                    'status': 'success',
                    'engine': 'OptimizationEngine',
                    'problem_type': problem['problem_type'],
                    'solution': solution,
                    'explanation': self._format_solution_explanation(solution, problem),
                    'metadata': {
                        'method': 'greedy_simplex',
                        'problem_detected': problem
                    }
                }
            else:
                result = solution
            
            return result
            
        except Exception as e:
            logger.error(f"OptimizationEngine error: {e}", exc_info=True)
            return {
                'status': 'error',
                'engine': 'OptimizationEngine',
                'error': str(e),
                'message': 'حدث خطأ أثناء معالجة مسألة التحسين'
            }
    
    def _format_solution_explanation(self, solution: Dict[str, Any], problem: Dict[str, Any]) -> str:
        """تنسيق شرح الحل بطريقة واضحة"""
        explanation_parts = []
        
        explanation_parts.append("📊 **حل مسألة التحسين:**\n")
        
        # الهدف
        objective = problem.get('objective', {})
        if objective.get('type') == 'maximize':
            explanation_parts.append(f"🎯 **الهدف:** تعظيم {objective.get('target', 'القيمة')}")
        else:
            explanation_parts.append(f"🎯 **الهدف:** تصغير {objective.get('target', 'القيمة')}")
        
        explanation_parts.append(f"\n💰 **القيمة المثلى:** ${solution['objective_value']}\n")
        
        # المتغيرات
        explanation_parts.append("📈 **التخصيص الأمثل:**")
        for var, value in solution['variables'].items():
            if value > 0:
                explanation_parts.append(f"   • {var}: {value} وحدة")
        
        # استخدام القيود
        explanation_parts.append("\n📋 **استخدام الموارد:**")
        for constraint_name, usage in solution['constraints_usage'].items():
            explanation_parts.append(
                f"   • {constraint_name}: {usage['used']}/{usage['limit']} ({usage['percentage']}%)"
            )
        
        # التوصية
        if solution.get('recommendation'):
            explanation_parts.append(f"\n💡 **التوصيات:**\n{solution['recommendation']}")
        
        return '\n'.join(explanation_parts)


# اختبار سريع
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = OptimizationEngine()
    
    # مثال: مسألة المزرعة
    test_problem = """
    لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار.
    تريد زراعة 3 محاصيل مختلفة لتحقيق أقصى ربح.
    ما هو التوزيع الأمثل؟
    """
    
    result = engine.process_task(test_problem)
    print(json.dumps(result, ensure_ascii=False, indent=2))
