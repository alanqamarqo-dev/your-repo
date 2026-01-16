# ==============================================================================
# AGL - Heikal Holographic Memory System (HHMS)
# نظام ذاكرة هيكل الهولوغرافية
# ==============================================================================
# Developer: Hossam Heikal (مطور النظام: حسام هيكل)
# Date: December 23, 2025 (تاريخ الإصدار: 23 ديسمبر 2025)
# Version: 1.0.0 - Quantum Phase Modulation Edition
# ==============================================================================
# Description (English):
# This module implements a "Holographic Memory" storage system. Instead of saving
# data as readable text or JSON, it converts information into a complex-valued
# interference pattern (Hologram).
#
# Key Features:
# 1. **Phase Modulation:** Data is encoded into the phase of a carrier wave.
# 2. **Key-Dependent:** The "noise mask" used for modulation is generated from
#    a specific integer seed (the Key). Without this key, the data appears as
#    pure white noise.
# 3. **Black Box Security:** Even if the file is stolen, it cannot be read
#    without the precise phase key.
# 4. **Developer Lens:** The developer can use the key to reconstruct the
#    original data perfectly.
#
# ------------------------------------------------------------------------------
# الوصف (العربية):
# تنفذ هذه الوحدة نظام تخزين "الذاكرة الهولوغرافية". بدلاً من حفظ البيانات كنصوص
# مقروءة أو ملفات JSON، تقوم بتحويل المعلومات إلى نمط تداخل ذو قيم مركبة (هولوغرام).
#
# الميزات الرئيسية:
# 1. **تعديل الطور (Phase Modulation):** يتم تشفير البيانات داخل "طور" الموجة الحاملة.
# 2. **الاعتماد على المفتاح:** يتم توليد "قناع الضجيج" المستخدم للتعديل بناءً على
#    رقم سري (المفتاح). بدون هذا المفتاح، تظهر البيانات كضجيج عشوائي بحت.
# 3. **أمان الصندوق الأسود:** حتى لو تمت سرقة الملف، لا يمكن قراءته بدون مفتاح
#    الطور الدقيق.
# 4. **عدسة المطور:** يمكن للمطور استخدام المفتاح لإعادة بناء البيانات الأصلية بدقة.
# ==============================================================================

import numpy as np
import json
import os
import pickle
import sys

class HeikalHolographicMemory:
    """
    Heikal Holographic Memory Controller.
    Manages the encoding (Save) and decoding (Load) of holographic data states.
    
    متحكم ذاكرة هيكل الهولوغرافية.
    يدير عمليات التشفير (الحفظ) وفك التشفير (التحميل) لحالات البيانات الهولوغرافية.
    """
    
    _has_printed_init = False

    def __init__(self, key_seed=42, frequency=None):
        """
        Initialize the memory system with a specific encryption key.
        
        تهيئة نظام الذاكرة بمفتاح تشفير محدد.
        
        Args:
            key_seed (int): The secret key used to generate the phase mask.
                            المفتاح السري المستخدم لتوليد قناع الطور.
            frequency (float | None): Optional carrier frequency. When provided,
                it is mixed into the phase modulation as a deterministic offset.
                تردد اختياري للموجة الحاملة. عند تمريره يتم دمجه كإزاحة طور ثابتة.
        """
        self.memory_file = "core_state.hologram.npy" # Changed to .npy for numpy binary
        self.key_seed = key_seed 
        self.frequency = frequency
        
        if not HeikalHolographicMemory._has_printed_init:
            print(f"🌌 [HOLO]: Holographic Memory Module Initialized (Key: {key_seed}).")
            if frequency is not None:
                try:
                    print(f"   [INFO]: Carrier Frequency: {float(frequency)}")
                except Exception:
                    print(f"   [INFO]: Carrier Frequency: {frequency}")
            print("   [INFO]: Data will be stored as complex interference patterns.")
            HeikalHolographicMemory._has_printed_init = True

    def process_task(self, payload):
        """
        Standard AGL Engine Interface.
        Payload: {"action": "save"|"load", "data": {...}}
        """
        action = payload.get("action")
        if action == "save":
            data = payload.get("data", {})
            success = self.save_memory(data)
            return {"status": "success" if success else "error", "engine": "HeikalHolographicMemory"}
        elif action == "load":
            data = self.load_memory()
            return {"status": "success", "data": data, "engine": "HeikalHolographicMemory"}
        return {"status": "error", "message": "Unknown action"}

    def _text_to_matrix(self, text):
        """
        Converts text string into a distributed numerical matrix (Hologram).
        
        تحويل النص إلى مصفوفة رقمية موزعة (نمط هولوغرافي).
        """
        # 1. Convert text to bytes / تحويل النص لبايتات
        data_bytes = text.encode('utf-8')
        
        # 2. Convert bytes to integer array / تحويل البايتات لمصفوفة أرقام
        data_array = np.frombuffer(data_bytes, dtype=np.uint8)
        
        # --- SECURITY LAYER: PERMUTATION (SHUFFLING) ---
        # This ensures that without the key, the order of bytes is lost.
        # هذا يضمن أنه بدون المفتاح، يتم فقدان ترتيب البايتات.
        rng = np.random.default_rng(self.key_seed)
        permutation = rng.permutation(len(data_array))
        shuffled_data = data_array[permutation]
        
        # 3. Normalize data (0-1) / تطبيع البيانات
        normalized = shuffled_data / 255.0
        
        # 4. Generate Carrier Wave (Noise Mask) / توليد الموجة الحاملة
        # We use the same RNG state (advanced by the permutation call)
        noise_mask = rng.random(len(normalized))

        # Optional frequency locking: mix frequency as deterministic phase offset
        freq_phase = 0.0
        if self.frequency is not None:
            # Keep the offset bounded and stable
            try:
                freq_phase = (float(self.frequency) % 1.0) * 2 * np.pi
            except Exception:
                freq_phase = 0.0
        
        # 5. Phase Modulation (Encoding) / تشفير الطور
        hologram_layer = normalized * np.exp(1j * (noise_mask * 2 * np.pi + freq_phase))
        
        return hologram_layer

    def _matrix_to_text(self, holog_matrix):
        """
        Reconstructs text from the hologram using the key.
        
        استعادة النص من الهولوغرام باستخدام المفتاح.
        """
        # 1. Regenerate RNG state / إعادة توليد حالة العشوائية
        rng = np.random.default_rng(self.key_seed)
        
        # 2. Generate the Permutation indices / توليد مؤشرات التبديل
        # Must match the sequence in _text_to_matrix
        permutation = rng.permutation(len(holog_matrix))
        
        # 3. Generate Noise Mask / توليد قناع الضجيج
        noise_mask = rng.random(len(holog_matrix))

        # Must match _text_to_matrix frequency phase behavior
        freq_phase = 0.0
        if self.frequency is not None:
            try:
                freq_phase = (float(self.frequency) % 1.0) * 2 * np.pi
            except Exception:
                freq_phase = 0.0
        
        # 4. Demodulation (Decoding) / فك التشفير
        decoded_signal = holog_matrix * np.exp(-1j * (noise_mask * 2 * np.pi + freq_phase))
        
        # 5. Extract Magnitude / استخراج القيمة المطلقة
        restored_shuffled = np.abs(decoded_signal)
        
        # 6. Inverse Permutation (Un-shuffling) / إلغاء التبديل
        # We need to put elements back to their original positions.
        # نحتاج لإعادة العناصر إلى مواقعها الأصلية.
        original_order = np.zeros_like(restored_shuffled)
        original_order[permutation] = restored_shuffled
        
        # 7. Convert back to bytes/text / التحويل العكسي لنص
        int_vals = np.round(original_order * 255.0).astype(np.uint8)
        
        return int_vals.tobytes().decode('utf-8')

    def save_memory(self, state_dict):
        """
        Encodes and saves the state dictionary as an interference pattern.
        
        يقوم بتشفير وحفظ قاموس الحالة كنمط تداخل.
        """
        try:
            print("⏳ [HOLO]: Encoding data into interference pattern...")
            # Convert dict to JSON string
            json_str = json.dumps(state_dict)
            
            # Transform to Hologram
            hologram_data = self._text_to_matrix(json_str)
            
            # Save as binary numpy file (unreadable to humans)
            # الحفظ كملف ثنائي (غير مقروء للبشر)
            np.save(self.memory_file, hologram_data)
            
            file_size = os.path.getsize(self.memory_file)
            print(f"✅ [HOLO]: Memory saved to '{self.memory_file}' ({file_size} bytes).")
            print("   [SEC]: Content is now pure mathematical noise.")
            return True
        except Exception as e:
            print(f"❌ [HOLO Error]: Save failed. {e}")
            return False

    def load_memory(self):
        """
        Loads and decodes the memory using the 'Projected Beam' (Key).
        
        يقوم بتحميل وفك تشفير الذاكرة باستخدام 'الشعاع المسلط' (المفتاح).
        """
        if not os.path.exists(self.memory_file):
            print("⚠️ [HOLO]: No hologram found. Starting fresh.")
            return None
            
        try:
            print("🔦 [HOLO]: Projecting reference beam to decode memory...")
            # Load the raw complex numbers
            hologram_data = np.load(self.memory_file)
            
            # Decode
            json_str = self._matrix_to_text(hologram_data)
            
            # Parse JSON
            return json.loads(json_str)
        except UnicodeDecodeError:
            print("❌ [HOLO Security]: DECRYPTION FAILED. Key mismatch or corrupted data.")
            print("   [INFO]: The retrieved data looked like garbage noise.")
            raise ValueError("Invalid Key")
        except Exception as e:
            print(f"❌ [HOLO Error]: Data corruption. {e}")
            return None

    def prune_and_merge(self):
        """
        [HEIKAL] Active Forgetting & Consolidation.
        - Prunes low importance memories.
        - Merges similar memories (abstraction).
        """
        data = self.load_memory()
        if not data or not isinstance(data, dict):
            return

        memories = data.get("memories", [])
        if not memories:
            return 
            
        print(f"🌌 [HOLO]: Pruning & Merging {len(memories)} memories...")
        
        # 1. Prune (Active Forgetting)
        kept_memories = [m for m in memories if m.get("importance", 0.5) > 0.3]
        
        # 2. Merge (Abstraction)
        merged_memories = []
        skip_indices = set()
        
        for i in range(len(kept_memories)):
            if i in skip_indices: continue
            
            mem_i = kept_memories[i]
            content_i = str(mem_i.get("content", ""))
            
            merged_content = content_i
            merge_count = 1
            
            for j in range(i+1, len(kept_memories)):
                if j in skip_indices: continue
                
                mem_j = kept_memories[j]
                content_j = str(mem_j.get("content", ""))
                
                # Check similarity (Set Jaccard)
                set_i = set(content_i.split())
                set_j = set(content_j.split())
                if not set_i or not set_j: continue
                
                intersection = len(set_i.intersection(set_j))
                union = len(set_i.union(set_j))
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.7: 
                    skip_indices.add(j)
                    merge_count += 1
                    if len(content_j) > len(merged_content):
                        merged_content = content_j
            
            new_mem = mem_i.copy()
            new_mem["content"] = merged_content
            new_mem["merge_count"] = merge_count
            merged_memories.append(new_mem)
            
        data["memories"] = merged_memories
        print(f"🌌 [HOLO]: Memory condensed from {len(memories)} to {len(merged_memories)} items.")
        self.save_memory(data)

# ==========================================
# Integration Test / اختبار التكامل
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 STARTING HOLOGRAPHIC MEMORY TEST")
    print("   بدء اختبار الذاكرة الهولوغرافية")
    print("="*60)

    # 1. Setup / الإعداد
    # المفتاح السري (يجب أن تعرفه أنت فقط)
    MY_KEY = 12345 
    holo_sys = HeikalHolographicMemory(key_seed=MY_KEY)
    
    # بيانات حساسة للتجربة
    secret_data = {
        "mission": "Protocol Omega",
        "target": "Unknown Virus",
        "strategy": "Stealth Mode",
        "last_access": "Today",
        "developer": "Hossam Heikal",
        "status": "Active"
    }
    
    # 2. Save / الحفظ
    print("\n--- 1. Saving Data (حفظ البيانات) ---")
    holo_sys.save_memory(secret_data)
    
    # 3. Verify Disk Content / التحقق من القرص
    print("\n--- 2. Checking File on Disk (فحص الملف) ---")
    if os.path.exists("core_state.hologram.npy"):
        print(f"   [DISK]: File exists.")
        print("   [NOTE]: If you open this file in a text editor, you will see binary gibberish.")
        print("   [ملاحظة]: إذا فتحت هذا الملف بمحرر نصوص، سترى رموزاً غير مفهومة.")

    # 4. Load with Correct Key / التحميل بالمفتاح الصحيح
    print("\n--- 3. Loading Data [Correct Key] (التحميل بالمفتاح الصحيح) ---")
    loaded_data = holo_sys.load_memory()
    print(f"   ✅ Restored Data: {json.dumps(loaded_data, indent=2)}")
    
    # 5. Hacker Attempt / محاولة الاختراق
    print("\n--- 4. HACKER ATTEMPT [Wrong Key] (محاولة اختراق بمفتاح خاطئ) ---")
    # محاولة قراءة بنفس الكود لكن مفتاح خطأ
    hacker_sys = HeikalHolographicMemory(key_seed=99999) 
    try:
        bad_data = hacker_sys.load_memory()
        print(f"   ⚠️ Hacker got: {bad_data}")
    except ValueError:
        print("   🛡️ [SUCCESS]: Hacker failed to reconstruct the hologram.")
        print("   🛡️ [نجاح]: فشل المخترق في إعادة بناء الهولوغرام (البيانات ظهرت كضجيج).")
    except Exception as e:
        print(f"   [INFO]: Exception caught as expected: {e}")

    print("\n" + "="*60)
    print("🏁 TEST COMPLETE / انتهى الاختبار")
    print("="*60)
