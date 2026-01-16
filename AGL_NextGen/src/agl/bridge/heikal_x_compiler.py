import ast
import os
import sys

class HeikalXCompiler:
    """
    مترجم هيكل-X (AGI Compiler)
    يقوم بتحويل الأكواد البرمجية التقليدية إلى منطق موجي (Wave-Logic).
    Translates traditional Python code into Heikal-X Wave-Logic.
    """
    
    def __init__(self, runtime=None):
        self.runtime = runtime
        self.output_ops = []
        self.variables_in_wave = set()

    def compile(self, source_code: str):
        """
        تحويل الكود المصدري إلى عمليات Heikal-X.
        """
        tree = ast.parse(source_code)
        self.output_ops = []
        self.variables_in_wave = set()
        
        self.visit(tree)
        
        compiled_script = "\n".join(self.output_ops)
        return compiled_script

    def visit(self, node):
        """Simple AST Walker."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def visit_Assign(self, node):
        # Python: x = [True, False] -> Heikal-X: runtime.superpose('x', [True, False])
        target = node.targets[0].id
        if isinstance(node.value, ast.List):
            states = [ast.literal_eval(elt) for elt in node.value.elts]
            self.output_ops.append(f"runtime.superpose('{target}', {states})")
            self.variables_in_wave.add(target)
        else:
            val = ast.literal_eval(node.value)
            self.output_ops.append(f"runtime.declare('{target}', {val})")

    def visit_If(self, node):
        # Python: if x: ... else: ... -> Heikal-X: runtime.wave_if('x', true_branch, false_branch)
        if isinstance(node.test, ast.Name):
            cond_var = node.test.id
            if cond_var in self.variables_in_wave:
                # Capture branches as functions
                true_code = self.capture_body(node.body)
                false_code = self.capture_body(node.orelse) if node.orelse else "lambda: None"
                
                self.output_ops.append(f"runtime.wave_if('{cond_var}', {true_code}, {false_code})")
                return # Skip standard processing for this node
        
        self.generic_visit(node)

    def capture_body(self, body_nodes):
        """Converts a block of AST nodes into a lambda or function string."""
        # Simple implementation for POC
        ops = []
        for node in body_nodes:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
                    arg = node.value.args[0].id if isinstance(node.value.args[0], ast.Name) else node.value.args[0].value
                    ops.append(f"print('{arg}:', runtime.variables['{arg}'].value if '{arg}' in runtime.variables else '{arg}')")
        
        if not ops: return "lambda: None"
        return f"lambda: [{', '.join(ops)}]"

    def execute_compiled(self, compiled_code, runtime_instance):
        """Executes the generated Wave-Logic against a runtime."""
        # Use a dictionary that includes runtime for both globals AND locals to be safe
        exec_env = {'runtime': runtime_instance, 'print': print}
        exec(compiled_code, exec_env, exec_env)

if __name__ == "__main__":
    # Example Usage
    code_to_compile = """
decision = [True, False]
if decision:
    print(decision)
"""
    compiler = HeikalXCompiler()
    compiled = compiler.compile(code_to_compile)
    print("--- COMPILED HEIKAL-X OPS ---")
    print(compiled)
