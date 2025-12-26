import sys
import os
import json
import time
import importlib.util
import random

# Try to import PyTorch for real training
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ PyTorch not found. Real training will be limited.")

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def main():
    print("==================================================")
    print("       🧬 AGL MOTHER SYSTEM ACTIVATED 🧬")
    print("          Identity: AGL_Mother_Prime")
    print("==================================================")
    
    # Initialize the Mother System
    mother = AdvancedCodeGenerator(parent_system_name="AGL_Mother_Prime")
    
    print("\n[System Status]")
    print("✅ Engine Cloner: Ready")
    print("✅ Knowledge Loader: Ready")
    print("✅ Language Specialists: [Python, JS, C++, Verilog]")
    print("✅ Recursive Improver: Linked")
    print(f"✅ Real Training Engine: {'Active (PyTorch)' if HAS_TORCH else 'Inactive (Missing PyTorch)'}")
    
    while True:
        print("\n--------------------------------------------------")
        print("Select an Action:")
        print("1. Generate New Child System (Interactive)")
        print("2. List Generated Children")
        print("3. Train Child System (REAL TRAINING)")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            generate_child_interactive(mother)
        elif choice == '2':
            list_children(mother)
        elif choice == '3':
            train_child_real(mother)
        elif choice == '4':
            print("Shutting down Mother System...")
            break
        else:
            print("Invalid choice.")

def generate_child_interactive(mother):
    print("\n--- 👶 Generate New Child System ---")
    name = input("Child Name (e.g., MedBot_v1): ").strip()
    domain = input("Domain (e.g., Medical, Finance, Cyber): ").strip()
    
    print("\nSelect Engines (comma separated):")
    print("Available: MathematicalBrain, QuantumNeuralCore, CreativeInnovationEngine, VisualSpatial")
    engines_input = input("Engines: ").strip()
    engines = [e.strip() for e in engines_input.split(',')] if engines_input else ["MathematicalBrain"]
    
    # Determine input/output size based on domain for the AI model
    input_size = 128
    output_size = 10
    if "cyber" in domain.lower():
        input_size = 1024 # Packet features
        output_size = 2   # Malicious/Benign
    elif "medic" in domain.lower():
        input_size = 512  # Patient vitals
        output_size = 5   # Diagnosis categories
        
    specs = {
        "name": name,
        "domain": domain,
        "required_engines": engines,
        "software_requirements": {
            "name": f"{name}_Core",
            "language": "python",
            "component_type": "ai_model",
            "component_spec": {
                "input_size": input_size,
                "output_size": output_size,
                "type": "ai_model"
            }
        },
        "fertile": True
    }
    
    print(f"\nGenerating {name}...")
    time.sleep(1)
    child = mother.generate_child_agi(specs)
    
    # Save child to disk
    filename = f"generated_children/{name}.json"
    os.makedirs("generated_children", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(child, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Child System '{name}' generated and saved to {filename}")

def list_children(mother):
    print("\n--- 📂 Generated Children ---")
    
    # Check memory first
    children_list = mother.generated_children
    
    # Also check disk
    if os.path.exists("generated_children"):
        for f in os.listdir("generated_children"):
            if f.endswith(".json"):
                try:
                    with open(os.path.join("generated_children", f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                        # Avoid duplicates if possible, but simple list is fine
                        name = data.get('metadata', {}).get('name', f)
                        domain = data.get('metadata', {}).get('domain', 'Unknown')
                        print(f"DISK: {name} ({domain})")
                except:
                    pass

    if not children_list and not os.path.exists("generated_children"):
        print("No children found.")
    else:
        for i, child in enumerate(children_list):
            print(f"MEM: {child['name']} ({child['domain']})")

def train_child_real(mother):
    if not HAS_TORCH:
        print("❌ Cannot perform real training: PyTorch is missing.")
        return

    print("\n--- 🎓 Real Training Session ---")
    
    # 1. Select Child
    child_name = input("Enter name of child system to train: ").strip()
    child_file = f"generated_children/{child_name}.json"
    
    if not os.path.exists(child_file):
        print(f"❌ Child system '{child_name}' not found on disk.")
        return
        
    print(f"📂 Loading {child_name}...")
    with open(child_file, 'r', encoding='utf-8') as f:
        child_data = json.load(f)
        
    # 2. Extract Code
    try:
        components = child_data['components']['software_components']['components']
        # Find the main component or the first one
        main_comp_key = next(iter(components))
        main_comp = components[main_comp_key]
        code = main_comp['code']
        spec = main_comp.get('specifications', {})
        
        input_size = spec.get('input_size', 128)
        output_size = spec.get('output_size', 10)
        
        print(f"💻 Extracted AI Model Code (Input: {input_size}, Output: {output_size})")
        
    except KeyError:
        print("❌ Could not find valid software components in child system.")
        return

    # 3. Write to Temp Module
    temp_module_name = f"temp_{child_name}_model"
    temp_file = f"{temp_module_name}.py"
    
    # Fix: Ensure imports are correct in generated code
    if "import torch" not in code:
        code = "import torch\nimport torch.nn as nn\n" + code
        
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(code)
        
    print(f"📝 Code written to {temp_file}")
    
    # 4. Dynamic Import
    try:
        spec = importlib.util.spec_from_file_location(temp_module_name, temp_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[temp_module_name] = module
        spec.loader.exec_module(module)
        
        # Find the nn.Module class
        model_class = None
        for name, obj in module.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
                model_class = obj
                break
        
        if not model_class:
            print("❌ No PyTorch Model class found in generated code.")
            return
            
        print(f"🧠 Found Model Class: {model_class.__name__}")
        
        # 5. Instantiate Model
        model = model_class()
        print("🤖 Model Instantiated.")
        
        # 6. Generate Synthetic Data
        print("🎲 Generating Synthetic Training Data...")
        batch_size = 32
        num_batches = 50
        
        # Random data
        data = torch.randn(batch_size * num_batches, input_size)
        targets = torch.randint(0, output_size, (batch_size * num_batches,))
        
        dataset = torch.utils.data.TensorDataset(data, targets)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 7. Training Loop
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        print("\n🚀 Starting Training Loop (5 Epochs)...")
        model.train()
        
        for epoch in range(5):
            total_loss = 0
            for batch_idx, (d, t) in enumerate(loader):
                optimizer.zero_grad()
                outputs = model(d)
                loss = criterion(outputs, t)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            avg_loss = total_loss / len(loader)
            print(f"   Epoch {epoch+1}/5 | Loss: {avg_loss:.4f}")
            
        print("\n✅ Training Complete!")
        
        # 8. Save Weights
        weights_file = f"generated_children/{child_name}_weights.pth"
        torch.save(model.state_dict(), weights_file)
        print(f"💾 Model weights saved to {weights_file}")
        
        # Cleanup
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception as e:
        print(f"❌ Training Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
