import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    print("1. Importing Core_Consciousness...")
    import Core_Consciousness
    from Core_Consciousness import create_engine
    
    print("2. Creating Consciousness Service...")
    # We pass None for bridge/registry as they are optional
    service = create_engine()
    
    print("3. Inspecting Initial State...")
    if service.self_model:
        print(f"   - Self Model: {service.self_model}")
        if hasattr(service.self_model, 'emotion_model'):
            em = service.self_model.emotion_model
            print(f"   - Initial Emotion: Valence={em.valence}, Arousal={em.arousal}")
    else:
        print("   - Self Model is None!")

    print("\n4. Running Consciousness Cycle...")
    service.start()
    print("   - Cycle completed.")

    print("\n5. Inspecting Post-Cycle State...")
    if service.self_model and hasattr(service.self_model, 'emotion_model'):
        em = service.self_model.emotion_model
        print(f"   - Current Emotion: Valence={em.valence}, Arousal={em.arousal}")
    
    # Check if we can trigger an update
    print("\n6. Triggering an Event (Simulated)...")
    if hasattr(service.self_model, 'emotion_model'):
        # Simulate a positive event
        event = {"sentiment": 0.8, "intensity": 0.5, "source": "test_script"}
        service.self_model.emotion_model.update_from_event(event)
        print("   - Event processed.")
        em = service.self_model.emotion_model
        print(f"   - New Emotion: Valence={em.valence}, Arousal={em.arousal}")
        
        if em.valence > 0:
            print("\nResult: Consciousness System is WORKING (State updated successfully).")
        else:
            print("\nResult: Consciousness System state did not update as expected.")
    else:
        print("   - self_model.emotion_model not found.")

except Exception as e:
    print(f"\nResult: Failed with error: {e}")
    import traceback
    traceback.print_exc()
