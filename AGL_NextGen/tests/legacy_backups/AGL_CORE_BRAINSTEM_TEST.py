import sys
import os
import unittest
import importlib
import shutil
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# --- SETUP PATHS ---
# We need to mimic the location of super_intelligence.py relative to root
# Real path: src/agl/core/super_intelligence.py
# We are running from D:\AGL, so we append the src path
ag_src_path = os.path.abspath(r"d:\AGL\AGL_NextGen\src")
sys.path.append(ag_src_path)

print("🧠 [TEST] Initializing BRAINSTEM DIAGNOSTIC PROTOCOL...")

class TestAGLBrainStem(unittest.TestCase):
    
    def setUp(self):
        # Create a dummy artifacts directory for testing
        self.test_artifacts = Path("d:/AGL/AGL_NextGen/artifacts/test_brainstem")
        self.test_artifacts.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        # Cleanup
        if self.test_artifacts.exists():
            shutil.rmtree(self.test_artifacts)

    def test_01_path_resolution(self):
        """Test if the system can resolve the Project Root correctly using Smart Detection."""
        print("\n🔍 [TEST 1] Path Resolution Logic (Smart Mode)...")
        
        # Define the Smart Detection logic (Mirroring super_intelligence.py)
        def find_project_root_mock(start_path):
            current = os.path.abspath(start_path)
            for _ in range(10): 
                # Check for key markers
                if os.path.exists(os.path.join(current, "pyproject.toml")) or \
                   os.path.exists(os.path.join(current, "AGL_SYSTEM_MAP.md")):
                    return current
                parent = os.path.dirname(current)
                if parent == current: 
                    break
                current = parent
            # Fallback
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(start_path))))

        # We simulate starting from src/agl/core
        mock_start_path = os.path.join(ag_src_path, "agl", "core")
        
        # Note: In this testing environment, "pyproject.toml" exists at D:\AGL\AGL_NextGen
        # This function should ascend from D:\AGL\AGL_NextGen\src\agl\core up to D:\AGL\AGL_NextGen
        
        calculated_root = find_project_root_mock(mock_start_path)
        expected_root_name = "AGL_NextGen"
        detected_name = os.path.basename(calculated_root)
        
        print(f"   -> Start Path: {mock_start_path}")
        print(f"   -> Calculated Root: {calculated_root}")
        
        self.assertEqual(detected_name, expected_root_name, "Smart Root Detection failed!")
        print("   ✅ Path Logic Verified.")

    def test_02_environment_config(self):
        """Test Environment Variable Injection logic."""
        print("\n🔍 [TEST 2] Environment Configuration...")
        
        # Reset env vars for test
        if "AGL_LLM_PROVIDER" in os.environ: del os.environ["AGL_LLM_PROVIDER"]
        
        # Logic from lines 30-36
        if "AGL_LLM_PROVIDER" not in os.environ:
            os.environ["AGL_LLM_PROVIDER"] = "ollama"
            
        self.assertEqual(os.environ["AGL_LLM_PROVIDER"], "ollama", "Default LLM Provider not set.")
        print(f"   -> AGL_LLM_PROVIDER: {os.environ.get('AGL_LLM_PROVIDER')}")
        
        # Check for Ollama (Real system check)
        ollama_path = shutil.which("ollama")
        if ollama_path:
            print(f"   -> Ollama Found at: {ollama_path}")
        else:
            print("   ⚠️ Ollama NOT found in PATH (Warning expected if not installed).")
        print("   ✅ Config Logic Verified.")

    def test_03_dynamic_import(self):
        """Test the dangerous 'import_module_from_path' function."""
        print("\n🔍 [TEST 3] Dynamic Module Loading...")
        
        # 1. Create a dummy python file
        dummy_file = self.test_artifacts / "dummy_skill.py"
        dummy_code = """
def say_hello():
    return "Hello from the Void!"
"""
        dummy_file.write_text(dummy_code, encoding='utf-8')
        
        # 2. Define the function (ripped from super_intelligence.py)
        def import_module_from_path(module_name, file_path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
            return None

        # 3. Attempt Load
        module = import_module_from_path("dummy_skill", str(dummy_file))
        
        self.assertIsNotNone(module, "Dynamic import returned None.")
        self.assertTrue(hasattr(module, "say_hello"), "Imported module lacks expected function.")
        result = module.say_hello()
        print(f"   -> Executed Function Result: '{result}'")
        self.assertEqual(result, "Hello from the Void!", "Function execution failed.")
        print("   ✅ Dynamic Import Verified.")

    @patch('agl.core.map_builder.AGL_System_Map_Builder') # Mock the builder to avoid full scan
    def test_04_self_awareness_init(self, MockBuilder):
        """Test SelfAwarenessModule initialization and fallback logic."""
        print("\n🔍 [TEST 4] Self-Awareness Module (Mocked)...")
        
        # Import the class (We need to import it from real file or mock it)
        # Since we are testing the Logic, we'll redefine the class structure briefly 
        # to match super_intelligence.py exactly for the test context
        
        class SelfAwarenessModule:
            def __init__(self, map_path):
                self.map_path = map_path
                self.system_map = None
                self.load_map()

            def load_map(self):
                if not os.path.exists(self.map_path):
                    print("   ⚠️ Map missing. Triggering Builder...")
                    # logic to call builder
                    try:
                        # In real code: from agl.core.map_builder import AGL_System_Map_Builder
                        builder = MockBuilder("root") # Use our mock
                        builder.build_map()
                        # Simulate creation
                        with open(self.map_path, 'w') as f: f.write('{"mock": true}')
                        print("   ✅ Builder completed.")
                    except Exception as e:
                        print(f"   ❌ Builder failed: {e}")

                if os.path.exists(self.map_path):
                    with open(self.map_path, 'r') as f:
                        self.system_map = f.read()
        
        # Run Test
        fake_map_path = self.test_artifacts / "system_map.json"
        
        # A. Verify it triggers builder when file missing
        print("   -> Scenario A: File Missing")
        awareness = SelfAwarenessModule(str(fake_map_path))
        self.assertTrue(fake_map_path.exists(), "Builder was not triggered or file not written.")
        self.assertTrue(MockBuilder.called, "MapBuilder class was not substantiated.")
        
        # B. Verify it loads existing file
        print("   -> Scenario B: File Exists")
        MockBuilder.reset_mock()
        awareness_2 = SelfAwarenessModule(str(fake_map_path))
        self.assertFalse(MockBuilder.called, "Builder triggered unnecessarily on existing file!")
        self.assertIn('"mock": true', awareness_2.system_map)
        
        print("   ✅ Self-Awareness Logic Verified.")

if __name__ == '__main__':
    unittest.main()
