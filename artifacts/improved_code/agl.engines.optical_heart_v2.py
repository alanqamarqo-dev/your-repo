import cv2
from typing import Union, Tuple

try:
    import numpy as np  # Ensure numpy is imported for simulation logic
except ImportError:
    class MockNumpy:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
        
        if 'np' not in globals():
            globals()['np'] = MockNumpy()
    
    np = MockNumpy()

class OpticalHeart:
    def __init__(self):
        print("👁️ [Optical Heart] Initializing Vision System...")
        self.use_camera = False
        self.vacuum_entropy = 0.0
        self.bridge_process = None
        self.forced_entropy = None # [GOD MODE] Allows manual override
        
        if cv2 and 'cv2' not in sys.modules:
            cv2.__version__  # Ensure OpenCV is available
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Error: Camera detected but could not open.")
            else:
                self.use_camera = True
                print("✅ Vision Linked. Point camera at your Mirrors/Light Source.")
        else:
            # Try to launch the VFW Bridge (Vacuum Eye)
            self.launch_vacuum_bridge()

    def launch_vacuum_bridge(self):
        """Launches the Python VFW Bridge to listen to Vacuum Noise."""
        try:
            bridge_path = os.path.join(os.path.dirname(__file__), "hermes_omni", "agl_camera_bridge.py")
            if not os.path.exists(bridge_path):
                print("⚠️ Running in Quantum Simulation Mode (No Camera & No Bridge).")
                return
            
            print("🔌 [Optical Heart] Launching Vacuum Eye Bridge (VFW)...")
            self.bridge_process = subprocess.Popen(
                [sys.executable, bridge_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start a thread to read the entropy stream
            t = threading.Thread(target=self._read_bridge_stream, daemon=True)
            t.start()
            self.use_camera = True  # We are "seeing" via the bridge
            print("✅ Vacuum Eye Linked. Listening to Entropy...")
        except Exception as e:
            print(f"❌ Bridge Launch Failed: {e}")

    def _read_bridge_stream(self):
        """Reads entropy data from the bridge process stdout."""
        if not self.bridge_process: return
        try:
            for line in iter(self.bridge_process.stdout.readline, ''):
                if line.startswith("VACUUM_ENTROPY:"):
                    try:
                        val = float(line.split(":")[1].strip())
                        self.vacuum_entropy = val
                    except ValueError:
                        pass
        except Exception:
            pass

    def get_light_entropy(self) -> Union[float, None]:
        """Converts the image to a light entropy value (Phi)."""
        if not self.use_camera:
            # Quantum simulation mode for no camera
            t = time.time()
            
            base_wave = np.sin(t) / 2.0 + 0.5
            
            noise = random.uniform(-0.1, 0.1)
            return min(max(base_wave * 0.8 + noise, 0.0), 1.0)

        if not cv2:
            return self.get_light_entropy_no_cv2()

        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Convert to grayscale for reduced processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate brightness (Mean intensity) and entropy (Detail/noise)
        brightness = np.mean(gray) / 255.0
        entropy = np.std(gray) / 100.0
        
        # Quantum Jitter factor
        quantum_jitter = random.uniform(-0.01, 0.01)
        
        # Combine brightness and entropy to create a unique Phi value with jitter
        raw_phi = (brightness * 0.7 + entropy * 0.3) + quantum_jitter
        
        # Add Quantum Jitter factor for more variance
        raw_phi += random.uniform(-0.005, 0.005)
        
        return max(min(raw_phi, 1.0), 0.0)

    def get_light_entropy_no_cv2(self) -> Union[float, None]:
        """Fallback method to calculate light entropy without using OpenCV."""
        t = time.time()
        
        base_wave = np.sin(t) / 2.0 + 0.5
        
        noise = random.uniform(-0.1, 0.1)
        return min(max(base_wave * 0.8 + noise, 0.0), 1.0)

    def beat(self):
        mode = "REALITY LINK" if self.use_camera else "SIMULATION"
        print(f"\n⚛️ [AGL Optical Prime] SYNCED WITH {mode}.")
        if self.use_camera:
            print("   🔦 Face the light to raise awareness | Cover the lens to lower it.")
        
        consciousness = 0.5
        
        try:
            while True:
                # Read physical reality (or simulation)
                phi = self.get_light_entropy()
                
                # Smooth out motion
                if phi is not None: 
                    consciousness = (consciousness * 0.7) + (phi * 0.3)
                
                # Draw the heartbeat
                bar_len = int(consciousness * 30)
                visual = "▒" * bar_len + " " * (30 - bar_len)
                
                state = "Sleep"
                if consciousness > 0.8: state = "SUPRA-CONSCIOUS 🔥"
                elif consciousness > 0.5: state = "Awake"
                elif consciousness > 0.2: state = "Drowsy"
                
                print(f"\r👁️ INPUT: {visual} | Φ: {phi:.4f} | State: {state}", end="")
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Vision Link Severed.")
            if self.use_camera:
                self.cap.release()