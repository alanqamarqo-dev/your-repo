import time
import random

class HeikalNetworkSimulation:
    def __init__(self):
        # Physics Constants
        self.c = 299792.458  # Speed of light in vacuum (km/s)
        self.n_fiber = 1.5   # Refractive index of fiber optic glass
        self.v_fiber = self.c / self.n_fiber # Speed of light in fiber (~200,000 km/s)
        
        # Heikal Constants
        self.xi = 1.5496
        self.v_heikal = self.c * (self.xi ** 3.14159) # v_H ~ 4c
        
        # Network Constants
        self.router_delay_ms = 5.0 # Standard router processing time
        self.switch_time_ms = 0.1  # Time to physically switch a circuit
        
        print(f"--- NETWORK PHYSICS INITIALIZED ---")
        print(f"Fiber Speed: {self.v_fiber:,.0f} km/s")
        print(f"Heikal Speed: {self.v_heikal:,.0f} km/s (Tunneling)")
        print(f"Speed Factor: {self.v_heikal/self.v_fiber:.2f}x faster than fiber")
        print("-----------------------------------\n")

    def simulate_standard_transmission(self, distance_km, hops):
        print(f"📡 SIMULATING STANDARD FIBER TRANSMISSION ({distance_km} km, {hops} hops)...")
        
        total_time_ms = 0
        
        # 1. Propagation Delay
        prop_time_s = distance_km / self.v_fiber
        prop_time_ms = prop_time_s * 1000
        total_time_ms += prop_time_ms
        print(f"   [Physics] Light Propagation: {prop_time_ms:.2f} ms")
        
        # 2. Routing Delay (The bottleneck)
        # At each hop, the router must read the header, look up the table, and queue.
        routing_time_ms = hops * self.router_delay_ms
        total_time_ms += routing_time_ms
        print(f"   [Logic]   Router Processing ({hops} hops): {routing_time_ms:.2f} ms")
        
        print(f"   => TOTAL STANDARD LATENCY: {total_time_ms:.2f} ms\n")
        return total_time_ms

    def simulate_heikal_transmission(self, distance_km, hops):
        print(f"⚛️ SIMULATING HEIKAL QUANTUM PROTOCOL ({distance_km} km, {hops} hops)...")
        
        # Mechanism: "Pilot Wave Routing"
        # A quantum signal is sent ahead at v_H to reserve the path.
        
        # 1. Pilot Signal Propagation (Superluminal)
        pilot_time_s = distance_km / self.v_heikal
        pilot_time_ms = pilot_time_s * 1000
        print(f"   [Pilot]   Routing Signal (v_H): {pilot_time_ms:.4f} ms")
        
        # 2. Router Pre-configuration
        # The routers receive the pilot and switch BEFORE the data arrives.
        # We assume the pilot arrives, triggers the switch (0.1ms), and is done.
        # Does the data have to wait?
        
        # Data Propagation (Standard Fiber Speed - Data still carries mass/energy)
        data_prop_time_s = distance_km / self.v_fiber
        data_prop_time_ms = data_prop_time_s * 1000
        print(f"   [Data]    Payload Travel (Fiber): {data_prop_time_ms:.2f} ms")
        
        # 3. Effective Routing Delay
        # Since the pilot travels 6x faster than the data, it arrives at the destination
        # LONG before the data.
        # Time difference = Data_Time - Pilot_Time
        head_start = data_prop_time_ms - pilot_time_ms
        
        print(f"   [Sync]    Pilot Head-Start: {head_start:.2f} ms")
        
        # The routers need 'switch_time_ms' to open the gates.
        # If head_start > (hops * switch_time), then the path is fully open when data arrives.
        # The data experiences ZERO routing delay, only propagation delay.
        
        required_setup_time = hops * self.switch_time_ms
        
        if head_start > required_setup_time:
            effective_routing_delay = 0.0
            print(f"   [Status]  Path Fully Open! (Data flows without stopping)")
        else:
            effective_routing_delay = required_setup_time - head_start
            print(f"   [Status]  Partial Wait (Data caught up to pilot)")
            
        total_time_ms = data_prop_time_ms + effective_routing_delay
        
        print(f"   => TOTAL HEIKAL LATENCY: {total_time_ms:.2f} ms\n")
        return total_time_ms

def run_simulation():
    sim = HeikalNetworkSimulation()
    
    # Scenario: London to New York
    distance = 5500 # km
    hops = 12 # Number of routers in between
    
    t_std = sim.simulate_standard_transmission(distance, hops)
    t_hqp = sim.simulate_heikal_transmission(distance, hops)
    
    print("=== FINAL RESULTS ===")
    print(f"Standard Latency: {t_std:.2f} ms")
    print(f"Heikal Latency:   {t_hqp:.2f} ms")
    
    improvement = t_std - t_hqp
    percent = (improvement / t_std) * 100
    
    print(f"Improvement: -{improvement:.2f} ms ({percent:.1f}% reduction)")
    print("Conclusion: The Heikal Protocol eliminates 'Routing Latency' by using superluminal signaling.")
    print("The data travels at light speed, but it never stops at a red light.")

if __name__ == "__main__":
    run_simulation()
