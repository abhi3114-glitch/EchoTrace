import numpy as np
from processor import SignalProcessor
from scipy.signal import chirp

def test_processor():
    rate = 44100
    proc = SignalProcessor(rate)
    
    # Generate a reference chirp
    duration = 0.005
    f0 = 2000
    f1 = 8000
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    ref_chirp = chirp(t, f0=f0, f1=f1, t1=duration, method='linear')
    window = np.hanning(len(ref_chirp))
    ref_chirp *= window
    
    # Simulate a received signal with delay
    # Delay of 0.01s (approx 1.7 meters at 343m/s ... wait 0.01 * 343 / 2 = 1.7m)
    # distance = t * c / 2
    # 1.7m -> 3.4m round trip -> 0.01s
    
    total_len = int(rate * 0.1) # 100ms buffer
    rec_buffer = np.zeros(total_len)
    
    # 1. Direct path at t=0.001s (close)
    t0_idx = int(0.001 * rate)
    rec_buffer[t0_idx : t0_idx+len(ref_chirp)] += ref_chirp * 1.0
    
    # 2. Echo at t=0.006s (5ms later) -> Delta 5ms
    # Distance = 0.005 * 343 / 2 = 0.85 approx
    t1_idx = int(0.006 * rate)
    rec_buffer[t1_idx : t1_idx+len(ref_chirp)] += ref_chirp * 0.3 # Weaker
    
    # Add noise
    rec_buffer += np.random.normal(0, 0.01, size=total_len)
    
    print("Running processor test...")
    dist, samples, corr = proc.find_echo_distance(rec_buffer, ref_chirp)
    
    print(f"Calculated Distance: {dist:.4f} m")
    print(f"Sample Delta: {samples}")
    
    # Expected: 5ms delta -> 0.005 * 343 / 2 = 0.8575 m
    expected = 0.005 * 343.0 / 2.0
    error = abs(dist - expected)
    print(f"Expected: {expected:.4f} m")
    
    if error < 0.05:
        print("TEST PASSED")
    else:
        print("TEST FAILED")

if __name__ == "__main__":
    test_processor()
