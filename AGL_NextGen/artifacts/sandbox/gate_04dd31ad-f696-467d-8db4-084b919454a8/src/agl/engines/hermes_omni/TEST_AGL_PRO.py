from AGL_Eyes_Pro import AGL_Eyes_Pro
import time
import sys

def main():
    print("\n🚀 STARTING HERMES OMNI - PROFESSIONAL EDITION")
    print("===============================================")
    
    # 1. تهيئة النظام (سيحاول تحميل C++ DLL)
    sensor = AGL_Eyes_Pro()
    
    print("\n📡 Scanning Bio-Field (Press Ctrl+C to stop)...\n")
    
    try:
        while True:
            # 2. قراءة البيانات (سواء من C++ أو Python)
            flux = sensor.scan(sensitivity=15)
            status = sensor.get_status_label(flux)
            
            # 3. عرض احترافي
            bar_len = int(flux * 2)
            bar = "█" * bar_len
            space = " " * (40 - bar_len)
            
            sys.stdout.write(f"\rFlux: [{bar}{space}] {flux:.4f} | Status: {status}")
            sys.stdout.flush()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 System Halted.")

if __name__ == "__main__":
    main()
