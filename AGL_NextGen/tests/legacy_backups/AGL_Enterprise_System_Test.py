import sys
import os
import json
import time

# Setup Path - Insert at BEGINNING to override site-packages
sys.path.insert(0, os.path.join(os.getcwd(), 'AGL_NextGen', 'src'))
sys.path.insert(0, os.path.join(os.getcwd(), 'repo-copy', 'Engineering_Engines'))

# from agl.core.super_intelligence import SuperIntelligence
from Advanced_Code_Generator import AdvancedCodeGenerator

def test_enterprise_evolution():
    print("🚀 INITIALIZING AGL ENTERPRISE EVOLUTION TEST...")
    
    # 1. Initialize SI (Disabled for Component Test)
    # si = SuperIntelligence()
    
    # 2. Force Goal
    complex_goal = "Build a Secure Hospital Management System with IoT for sensors, RBAC for doctors, audits, and automated penetration_testing."
    print(f"🎯 Goal Set: {complex_goal}")
    # si.add_goal(complex_goal)
    
    # 3. Initialize Engine (to ensure it's fresh)
    engine = AdvancedCodeGenerator()
    
    # 4. Manual Trigger (simulate the loop decision)
    print("⚙️  Simulating Volition -> Engine Link...")
    
    requirements = {
        "name": "Eagle_Hospital_System_V1",
        "description": "Secure Web Platform for Hospital Management with IoT sensors, RBAC, CRUD, and penetration test.",
        "domain": "healthcare",
        "spec": {"framework": "react"} # Hint for UI
    }
    
    result = engine.generate_software_system(requirements, verbose=True)
    
    # 5. Analyze verification
    components = result['components']
    print(f"\n📦 Generated {len(components)} Components:")
    for name, data in components.items():
        print(f"  - [{name}] ({data.get('language')}): {data.get('description')}")
        
    print("\n🔍 Deep Code Inspection:")
    
    # Check API Security
    api_code = components['backend_api']['code']
    if "has_role" in api_code and "get_current_user" in api_code:
        print("  ✅ Backend API: RBAC Middleware DETECTED")
    else:
        print("  ❌ Backend API: RBAC Middleware MISSING")

    if "@app.post(\"/patients/\")" in api_code:
        print("  ✅ Backend API: CRUD Operations DETECTED")
    else:
        print("  ❌ Backend API: CRUD Operations MISSING")
        print("DEBUG API CODE SNIPPET:")
        print(api_code[:1000])

    # Check Database
    db_code = components['database_model']['code']
    if "class Role(Base):" in db_code:
        print("  ✅ Database: Role-Based Access Control Models DETECTED")
    else:
        print("  ❌ Database: RBAC Models MISSING")
        print("DEBUG DB CODE SNIPPET:")
        print(db_code[:500])
        
    # Check Frontend
    ui_code = components['frontend_ui']['code']
    if "import React" in ui_code and "<AuthContext.Provider" in ui_code:
        print("  ✅ Frontend: React Structure & Auth Context DETECTED")
    else:
        print(f"  ❌ Frontend: React Code Missing (Got: {ui_code[:50]}...)")
        
    # Check IoT
    if 'iot_gateway' in components:
         print("  ✅ IoT Layer: Gateway DETECTED")
    else:
         print("  ❌ IoT Layer: MISSING")

    # Check Testing
    if 'security_scanner' in components:
        scanner_code = components['security_scanner']['code']
        if "SQL Injection" in scanner_code:
             print("  ✅ Security: Automated Pen-Tester DETECTED")
    else:
        print("  ❌ Security: Pen-Tester MISSING")

    return result

if __name__ == "__main__":
    test_enterprise_evolution()
