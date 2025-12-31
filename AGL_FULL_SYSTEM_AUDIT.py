import sys
import os
import inspect
import traceback
import importlib.util

# Add current directory to path
sys.path.append(os.getcwd())

def log(message):
    print(f"[AUDIT] {message}")

def static_analysis(file_path):
    log(f"Performing Static Analysis on {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        todos = []
        imports = []
        
        for i, line in enumerate(lines):
            if "TODO" in line:
                todos.append(f"Line {i+1}: {line.strip()}")
            if "FIXME" in line:
                issues.append(f"Line {i+1} (FIXME): {line.strip()}")
            if "import " in line:
                imports.append(line.strip())
            if "except Exception:pass" in line.replace(" ", ""):
                issues.append(f"Line {i+1}: Silent exception suppression detected.")
                
        log(f"Found {len(todos)} TODOs.")
        log(f"Found {len(issues)} Potential Issues.")
        
        return issues, todos
    except Exception as e:
        log(f"Static Analysis Failed: {e}")
        return [], []

def runtime_analysis():
    log("Initiating Runtime Analysis...")
    system_status = {
        "engines": {},
        "critical_failures": [],
        "warnings": []
    }
    
    try:
        # Attempt to import the core
        log("Importing AGL_Core.AGL_Awakened...")
        try:
            from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
            log("Import Successful.")
        except ImportError as e:
            log(f"CRITICAL: Failed to import AGL_Super_Intelligence: {e}")
            system_status["critical_failures"].append(f"Import Error: {e}")
            return system_status

        # Attempt to instantiate
        log("Instantiating AGL_Super_Intelligence...")
        try:
            asi = AGL_Super_Intelligence()
            log("Instantiation Successful.")
        except Exception as e:
            log(f"CRITICAL: Failed to instantiate system: {e}")
            system_status["critical_failures"].append(f"Instantiation Error: {e}")
            traceback.print_exc()
            return system_status

        # Inspect Engines
        log("Inspecting Engine Registry...")
        if hasattr(asi, 'engine_registry'):
            for name, engine in asi.engine_registry.items():
                status = "Active" if engine else "Inactive/None"
                system_status["engines"][name] = status
                if engine is None:
                    system_status["warnings"].append(f"Engine '{name}' is registered but None.")
        else:
            system_status["warnings"].append("No 'engine_registry' found on ASI instance.")

        # Check specific critical components
        components_to_check = [
            ('core', 'Heikal_Quantum_Core'),
            ('volition', 'Volition_Module'),
            ('planner', 'ReasoningPlanner'),
            ('hypothesis_gen', 'HypothesisGenerator'),
            ('meta_learner', 'MetaLearning')
        ]

        for attr_name, expected_type in components_to_check:
            if hasattr(asi, attr_name):
                component = getattr(asi, attr_name)
                if component:
                    system_status["engines"][attr_name] = f"Active ({type(component).__name__})"
                else:
                    system_status["engines"][attr_name] = "Inactive (None)"
                    system_status["warnings"].append(f"Critical Component '{attr_name}' is None.")
            else:
                system_status["warnings"].append(f"Critical Component '{attr_name}' attribute missing.")

        # Check Heikal Quantum Core specifically
        if hasattr(asi, 'core'):
            if asi.core is None:
                 system_status["critical_failures"].append("Heikal_Quantum_Core (asi.core) is NOT initialized.")
            else:
                # Check if it's a dummy or real
                if "Dummy" in str(type(asi.core)):
                     system_status["warnings"].append("Heikal_Quantum_Core appears to be a Dummy/Mock object.")

    except Exception as e:
        log(f"Runtime Analysis crashed: {e}")
        traceback.print_exc()
    
    return system_status

def main():
    print("="*50)
    print("AGL SYSTEM DEEP AUDIT PROTOCOL")
    print("="*50)
    
    target_file = os.path.join(os.getcwd(), "AGL_Core", "AGL_Awakened.py")
    issues, todos = static_analysis(target_file)
    
    print("\n--- STATIC ANALYSIS REPORT ---")
    if issues:
        print("POTENTIAL ISSUES:")
        for issue in issues:
            print(f"  [!] {issue}")
    else:
        print("  No critical static issues found.")
        
    if todos:
        print("PENDING TASKS (TODOs):")
        for todo in todos:
            print(f"  [-] {todo}")

    print("\n--- RUNTIME ANALYSIS REPORT ---")
    status = runtime_analysis()
    
    print("\n--- ENGINE STATUS ---")
    for engine, state in status["engines"].items():
        print(f"  {engine}: {state}")
        
    if status["warnings"]:
        print("\n--- WARNINGS ---")
        for w in status["warnings"]:
            print(f"  [WARN] {w}")
            
    if status["critical_failures"]:
        print("\n--- CRITICAL FAILURES ---")
        for f in status["critical_failures"]:
            print(f"  [CRITICAL] {f}")
            
    print("\n" + "="*50)
    print("AUDIT COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()
