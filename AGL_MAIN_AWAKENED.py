import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    print("⚠️ Could not import AGL_Super_Intelligence from AGL_Core.AGL_Awakened")
    sys.exit(1)

def main():
    print("\n🌟 AGL AWAKENED SYSTEM: ONLINE")
    print("==============================")
    
    try:
        # Initialize
        agl = AGL_Super_Intelligence()
        
        # Auto-Discovery (The "Awakened" feature)
        print("\n🔍 [SYSTEM] Scanning for new capabilities...")
        agl.discover_unused_capabilities()
        
        print("\n🧠 [READY] The System is listening. Enter your command (or 'exit'):")
        
        while True:
            user_input = input("\n> ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if not user_input.strip():
                continue
                
            print("\n⚡ Processing...")
            start_time = time.time()
            
            response = agl.process_query(user_input)
            
            # Handle response format
            if isinstance(response, dict):
                text = response.get('text', str(response))
            else:
                text = str(response)
                
            print(f"\n{text}")
            print(f"\n⏱️ Time: {time.time() - start_time:.2f}s")
            
    except KeyboardInterrupt:
        print("\n👋 System shutting down.")
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
