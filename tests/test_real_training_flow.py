import sys
import os
import json
import time
import importlib.util
import shutil

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_flow():
    print("🧪 Starting Automated Test of Real Training Feature...")
    
    # 1. Setup Mother
    mother = AdvancedCodeGenerator(parent_system_name="AGL_Mother_Test")
    
    # 2. Generate Child
    child_name = "AutoTrainBot"
    print(f"👶 Generating child: {child_name}...")
    
    specs = {
        "name": child_name,
        "domain": "Cybersecurity",
        "required_engines": ["MathematicalBrain"],
        "software_requirements": {
            "name": f"{child_name}_Core",
            "language": "python",
            "component_type": "ai_model",
            "component_spec": {
                "input_size": 64,
                "output_size": 2,
                "type": "ai_model"
            }
        },
        "fertile": True
    }
    
    child = mother.generate_child_agi(specs)
    
    # Save to disk (required for the training logic to load it)
    os.makedirs("generated_children", exist_ok=True)
    child_path = f"generated_children/{child_name}.json"
    with open(child_path, 'w', encoding='utf-8') as f:
        json.dump(child, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Child saved to {child_path}")
    
    # 3. Perform Training (Logic adapted from activate_mother_system.py)
    print("\n🎓 Initiating Training Sequence...")
    
    # Extract Code
    components = child['components']['software_components']['components']
    main_comp = components[next(iter(components))]
    code = main_comp['code']
    
    # Ensure imports
    if "import torch" not in code:
        code = "import torch\nimport torch.nn as nn\n" + code
        
    # Write temp file
    temp_module_name = f"temp_{child_name}_model"
    temp_file = f"{temp_module_name}.py"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(code)
        
    # Import
    spec = importlib.util.spec_from_file_location(temp_module_name, temp_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[temp_module_name] = module
    spec.loader.exec_module(module)
    
    # Find Class
    model_class = None
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
            model_class = obj
            break
            
    if not model_class:
        print("❌ Failed to find model class")
        return

    # Instantiate
    model = model_class()
    print(f"🤖 Model {model_class.__name__} instantiated.")
    
    # Determine input size dynamically
    input_size = 64 # Default
    for name, submod in model.named_modules():
        if isinstance(submod, nn.Linear):
            input_size = submod.in_features
            print(f"ℹ️ Detected input size from first Linear layer: {input_size}")
            break

    # Train
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()
    
    # Synthetic Data
    inputs = torch.randn(100, input_size)
    targets = torch.randint(0, 2, (100,))
    
    print("\n🚀 Training Progress:")
    model.train()
    for epoch in range(5):
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        print(f"   Epoch {epoch+1}: Loss = {loss.item():.4f}")
        
    print("\n✅ Test Complete: Training successful.")
    
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)
    if os.path.exists(child_path):
        os.remove(child_path)

if __name__ == "__main__":
    test_flow()
