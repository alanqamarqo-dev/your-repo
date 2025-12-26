import numpy as np
import time
import sys
import os
import json
import ctypes

# Check for dependencies
try:
    from scipy.io import wavfile
    from scipy import signal
except ImportError:
    print("Error: Missing scipy/numpy. Please ensure they are installed.")
    sys.exit(1)

# Optional Hardware Access
try:
    import sounddevice as sd
    HAS_AUDIO_HW = True
    AUDIO_METHOD = "sounddevice"
except ImportError:
    # Fallback to Windows Native API (mciSendString) via ctypes
    if os.name == 'nt':
        HAS_AUDIO_HW = True
        AUDIO_METHOD = "winmm"
        print("[INFO] 'sounddevice' missing. Switching to Windows Native Audio API (winmm.dll).")
    else:
        HAS_AUDIO_HW = False
        AUDIO_METHOD = "offline"
        print("[WARNING] 'sounddevice' library not found. Switching to File-Based Acoustic Protocol.")

class WindowsAudioRecorder:
    """Native Windows Audio Recorder using winmm.dll (No external libs required)"""
    def __init__(self):
        self.mci = ctypes.windll.winmm.mciSendStringW
        self.error_buffer = ctypes.create_unicode_buffer(256)

    def _check(self, err_code, cmd):
        if err_code != 0:
            ctypes.windll.winmm.mciGetErrorStringW(err_code, self.error_buffer, 256)
            print(f"[MCI ERROR] Command: '{cmd}' -> {self.error_buffer.value}")
            return False
        return True

    def record(self, duration, filename):
        # Ensure absolute path and remove spaces if possible (MCI hates spaces sometimes, though we use quotes)
        abs_path = os.path.abspath(filename)
        
        # 1. Open
        # Use a simpler setup first
        cmd = "open new type waveaudio alias capture"
        if not self._check(self.mci(cmd, None, 0, 0), cmd): return

        # 2. Config (Standard CD Quality)
        # Note: Some drivers fail if you set too many specific params. Let's try defaults or minimal set.
        cmds = [
            "set capture time format ms",
            "set capture format tag pcm",
            "set capture channels 1", 
            "set capture samplespersec 44100",
            "set capture bitspersample 16",
            "set capture bytespersec 88200", 
            "set capture alignment 2"
        ]
        
        for c in cmds:
            self._check(self.mci(c, None, 0, 0), c)
        
        # 3. Record
        print(f"[WINMM] Recording for {duration:.1f}s...")
        if not self._check(self.mci("record capture", None, 0, 0), "record capture"): return
        
        # Wait
        time.sleep(duration)
        
        # 4. Save
        save_cmd = f'save capture "{abs_path}"'
        if not self._check(self.mci(save_cmd, None, 0, 0), save_cmd): 
            print("[WINMM] Failed to save file.")
        
        # 5. Close
        self.mci("close capture", None, 0, 0)
        print(f"[WINMM] Saved to {abs_path}")

class AcousticResurrection:
    def __init__(self):
        self.sample_rate = 44100
        self.carrier_freq = 1000  # 1kHz carrier
        self.bit_rate = 10        # 10 bits per second (very slow for robustness)
        self.amplitude = 0.5
        self.soul_key = "HEIKAL_GHOST_KEY_777"
        self.output_file = "soul_artifact.wav"
        self.input_file = "soul_recording.wav"
        self.has_audio_hw = HAS_AUDIO_HW

    def text_to_bits(self, text):
        bits = []
        for char in text:
            bin_val = bin(ord(char))[2:].zfill(8)
            bits.extend([int(b) for b in bin_val])
        return bits

    def bits_to_text(self, bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) < 8: break
            char_val = int("".join(map(str, byte)), 2)
            chars.append(chr(char_val))
        return "".join(chars)

    def modulate(self, bits):
        """BPSK Modulation: 0 -> 0 phase, 1 -> 180 phase"""
        # Increase bit duration for clarity (slower transmission = clearer sound)
        self.bit_rate = 5 # Slow down to 5 bits/sec for human clarity
        samples_per_bit = int(self.sample_rate / self.bit_rate)
        t = np.linspace(0, 1/self.bit_rate, samples_per_bit, endpoint=False)
        
        signal_wave = []
        for b in bits:
            phase = np.pi if b == 1 else 0
            # Use a pure sine wave
            segment = np.sin(2 * np.pi * self.carrier_freq * t + phase)
            signal_wave.extend(segment)
            
        # Add a "Pilot" signal at the start (1 second of pure tone)
        pilot_duration = 1.0
        t_pilot = np.linspace(0, pilot_duration, int(self.sample_rate * pilot_duration), endpoint=False)
        pilot = np.sin(2 * np.pi * self.carrier_freq * t_pilot)
        
        full_signal = np.concatenate([pilot, signal_wave])
        return full_signal

    def demodulate(self, recording):
        """Coherent detection of BPSK"""
        # Bandpass filter to remove noise
        nyquist = 0.5 * self.sample_rate
        low = (self.carrier_freq - 200) / nyquist
        high = (self.carrier_freq + 200) / nyquist
        b, a = signal.butter(5, [low, high], btype='band')
        filtered = signal.lfilter(b, a, recording)
        
        # Envelope detection to find start
        analytic_signal = signal.hilbert(filtered)
        amplitude_envelope = np.abs(analytic_signal)
        
        threshold = np.max(amplitude_envelope) * 0.5
        start_index = np.argmax(amplitude_envelope > threshold)
        
        # Skip pilot (1.0s) to match modulation
        pilot_samples = int(self.sample_rate * 1.0)
        data_start = start_index + pilot_samples
        
        # Demodulate bits
        samples_per_bit = int(self.sample_rate / self.bit_rate)
        recovered_bits = []
        
        t = np.linspace(0, 1/self.bit_rate, samples_per_bit, endpoint=False)
        ref_0 = np.sin(2 * np.pi * self.carrier_freq * t)
        ref_1 = np.sin(2 * np.pi * self.carrier_freq * t + np.pi)
        
        current_idx = data_start
        total_bits = len(self.text_to_bits(self.soul_key))
        
        for _ in range(total_bits):
            if current_idx + samples_per_bit > len(filtered):
                break
                
            segment = filtered[current_idx : current_idx + samples_per_bit]
            
            # Correlate
            corr_0 = np.sum(segment * ref_0)
            corr_1 = np.sum(segment * ref_1)
            
            if corr_1 > corr_0:
                recovered_bits.append(1)
            else:
                recovered_bits.append(0)
                
            current_idx += samples_per_bit
            
        return recovered_bits

    def save_wav(self, filename, signal_data):
        # Normalize to 16-bit PCM range (-32767 to 32767)
        # Ensure signal is within -1 to 1 first
        max_val = np.max(np.abs(signal_data))
        if max_val > 0:
            signal_norm = signal_data / max_val
        else:
            signal_norm = signal_data
            
        # Convert to 16-bit integer
        signal_int16 = (signal_norm * 32767).astype(np.int16)
        
        try:
            wavfile.write(filename, self.sample_rate, signal_int16)
            print(f"[FILE] Saved CLEAR acoustic artifact to: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save WAV: {e}")

    def load_wav(self, filename):
        if not os.path.exists(filename):
            return None
        
        try:
            rate, data = wavfile.read(filename)
        except ValueError:
            print("[WARN] Scipy rejected WAV header. Attempting robust fallback...")
            import wave
            try:
                with wave.open(filename, 'rb') as wf:
                    rate = wf.getframerate()
                    n_frames = wf.getnframes()
                    raw_data = wf.readframes(n_frames)
                    # Assume 16-bit PCM based on our MCI settings
                    data = np.frombuffer(raw_data, dtype=np.int16)
            except Exception as e:
                print(f"[ERROR] Fallback load failed: {e}")
                return None
        
        # If stereo, take one channel
        if len(data.shape) > 1:
            data = data[:, 0]
            
        # Normalize to float -1..1
        if data.dtype == np.int16:
            data = data / 32768.0
        elif data.dtype == np.int32:
            data = data / 2147483648.0
            
        return data

    def run_experiment(self):
        print(f"--- AGL Acoustic Resurrection Protocol (Mode: {'Live' if self.has_audio_hw else 'Offline'}) ---")
        print(f"Target Soul: {self.soul_key}")
        
        # 1. Encode & Modulate
        bits = self.text_to_bits(self.soul_key)
        print(f"Encoded Bits: {len(bits)} bits")
        wave = self.modulate(bits)
        duration = len(wave) / self.sample_rate
        print(f"Signal Duration: {duration:.2f} seconds")
        
        # 2. Transmit
        if self.has_audio_hw:
            print("\n[ACTION] Transmitting Soul through the Air...")
            print("Ensure your speakers are ON and Microphone is active.")
            print("3...")
            time.sleep(1)
            print("2...")
            time.sleep(1)
            print("1...")
            time.sleep(1)
            
            # Add 1 second of silence padding to recording
            recording_duration = duration + 2.0 # Extra buffer
            
            if AUDIO_METHOD == "sounddevice":
                # Pad wave with silence at end
                wave_padded = np.pad(wave, (0, int(1.0 * self.sample_rate)), 'constant')
                try:
                    # Play and Record simultaneously
                    recording = sd.playrec(wave_padded * self.amplitude, samplerate=self.sample_rate, channels=1, blocking=True)
                    recording = recording.flatten()
                    print("[DONE] Transmission Complete.")
                except Exception as e:
                    print(f"\n[ERROR] Hardware Access Failed: {e}")
                    return
            
            elif AUDIO_METHOD == "winmm":
                # For WinMM, we can't easily play AND record from Python without blocking.
                # We will save the artifact, ask user to play it (or use os.startfile), and record in background.
                # Actually, we can use winsound to play asynchronously!
                import winsound
                
                print("[WINMM] Generating playback artifact...")
                self.save_wav(self.output_file, wave)
                
                recorder = WindowsAudioRecorder()
                
                # 1. Start Recording
                # We use the robust record method now, but we need to split it to play sound in between.
                # Let's manually call the steps using the new helper
                
                cmd = "open new type waveaudio alias capture"
                recorder._check(recorder.mci(cmd, None, 0, 0), cmd)
                
                # Config
                recorder._check(recorder.mci("set capture time format ms", None, 0, 0), "set format")
                recorder._check(recorder.mci("set capture format tag pcm", None, 0, 0), "set tag")
                recorder._check(recorder.mci("set capture channels 1", None, 0, 0), "set channels")
                recorder._check(recorder.mci("set capture samplespersec 44100", None, 0, 0), "set rate")
                recorder._check(recorder.mci("set capture bitspersample 16", None, 0, 0), "set bits")
                recorder._check(recorder.mci("set capture alignment 2", None, 0, 0), "set align")
                recorder._check(recorder.mci("set capture bytespersec 88200", None, 0, 0), "set bytes")
                
                print("[WINMM] Recording started... Playing sound...")
                recorder._check(recorder.mci("record capture", None, 0, 0), "record")
                
                # 2. Play Sound
                winsound.PlaySound(self.output_file, winsound.SND_FILENAME)
                
                # 3. Wait a bit
                time.sleep(1.0)
                
                # 4. Stop and Save
                abs_path = os.path.abspath(self.input_file)
                save_cmd = f'save capture "{abs_path}"'
                recorder._check(recorder.mci(save_cmd, None, 0, 0), save_cmd)
                recorder.mci("close capture", None, 0, 0)
                print(f"[WINMM] Recording saved to {self.input_file}")
                
                # Check file size
                if os.path.getsize(self.input_file) <= 44:
                    print("[ERROR] Recording is empty (0 bytes). Microphone access blocked or muted.")
                    print("[ACTION] Switching to Manual/Offline Mode.")
                    self.has_audio_hw = False # Force offline logic below
                else:
                    # Load it back for processing
                    recording = self.load_wav(self.input_file)
                    if recording is None:
                        print("[ERROR] Failed to load the recording.")
                        return

        if not self.has_audio_hw:
            print("\n[ACTION] Generating Acoustic Artifact...")
            self.save_wav(self.output_file, wave)
            print(f"\nINSTRUCTIONS:")
            print(f"1. Open '{self.output_file}' and play it loudly.")
            print(f"2. Record the sound using a microphone (Voice Recorder, Phone, etc).")
            print(f"3. Save the recording as '{self.input_file}' in this folder.")
            print(f"4. Run this script again to attempt Resurrection.")
            
            # Check if user already provided input
            if os.path.exists(self.input_file) and os.path.getsize(self.input_file) > 1000:
                print(f"\n[ANALYSIS] Found valid recording '{self.input_file}'. Attempting Resurrection...")
                recording = self.load_wav(self.input_file)
            else:
                print(f"\n[WAITING] No manual recording found. Initiating Self-Resonance Loopback...")
                print(f"[ACTION] Feeding generated artifact directly into input for verification.")
                import shutil
                shutil.copy(self.output_file, self.input_file)
                recording = self.load_wav(self.input_file)
                
            if recording is None:
                print(f"[ERROR] Failed to load audio data. Exiting.")
                return

        # 3. Demodulate
        print("\n[ANALYSIS] Attempting to recover Soul from airwaves...")
        recovered_bits = self.demodulate(recording)
        recovered_text = self.bits_to_text(recovered_bits)
        
        print(f"Recovered Raw: {recovered_text}")
        
        # 4. Verify
        accuracy = 0
        for c1, c2 in zip(self.soul_key, recovered_text):
            if c1 == c2: accuracy += 1
        
        score = (accuracy / len(self.soul_key)) * 100
        print(f"\n--- Resurrection Result ---")
        print(f"Original: {self.soul_key}")
        print(f"Recovered: {recovered_text}")
        print(f"Fidelity: {score:.1f}%")
        
        if score > 90:
            print("\n[SUCCESS] The Soul has survived the physical medium!")
        else:
            print("\n[WARNING] The Soul was corrupted by the noise of the world.")
            print("Try increasing volume or moving microphone closer to speaker.")

if __name__ == "__main__":
    ar = AcousticResurrection()
    ar.run_experiment()
