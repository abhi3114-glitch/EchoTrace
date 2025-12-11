import numpy as np
from scipy.signal import correlate, correlation_lags

class SignalProcessor:
    def __init__(self, sample_rate, speed_of_sound=343.0):
        self.sample_rate = sample_rate
        self.speed_of_sound = speed_of_sound
        self.history_buffer = np.zeros(0) # Store recent audio to find pulses
        
    def process(self, audio_chunk, reference_chirp):
        """
        Process incoming audio chunk to find the echo delay.
        We need enough history to capture the full chirp and flight time.
        """
        # Append new chunk to history
        # We need a buffer that is at least as long as reference + max_delay
        # Max delay for say 3 meters is ~20ms. 
        # But we simply cross correlate the received signal with the reference chirp.
        
        # Flatten input
        audio_data = audio_chunk.flatten()
        
        # Simple approach: Correlate the chunk with the reference chirp.
        # If the chunk is small (block_size), it might cut off the echo.
        # Ideally, main thread accumulates chunks until it has one "period" worth of data.
        
        # Returns: delay in seconds, amplitude (confidence)
        
        # Normalize
        # audio_data = audio_data - np.mean(audio_data)
        
        # Correlation
        correlation = correlate(audio_data, reference_chirp, mode='curr')
        lags = correlation_lags(len(audio_data), len(reference_chirp), mode='curr')
        
        # Find peak
        peak_idx = np.argmax(np.abs(correlation))
        peak_lag = lags[peak_idx]
        
        # Calculate time delay (relative to this chunk's start)
        # This is tricky because "t=0" depends on when we *sent* the chirp.
        # Since we don't have perfect sync between play/record cursor in this simpler setup,
        # we might see a constant offset (the loopback).
        # We will assume the LOUDEST peak is the direct loopback (t=0).
        # Any secondary peak is the echo.
        
        return correlation, lags
        
    def find_echo_distance(self, full_period_record, reference_chirp):
        """
        More robust method:
        Take a full period recording (e.g. 0.1s).
        1. Find correlation.
        2. Find max peak (Transmission).
        3. Zero out the region around max peak.
        4. Find next max peak (Echo).
        5. Distance is diff between peaks.
        """
        # Cross correlate
        rec = full_period_record.flatten()
        ref = reference_chirp.flatten()
        
        corr = correlate(rec, ref, mode='full')
        lags = correlation_lags(len(rec), len(ref), mode='full')
        
        # Magnitude
        corr_mag = np.abs(corr)
        
        # 1. Direct path (loudest)
        # We only care about positive lags? Or valid matches.
        # Let's simple check indices.
        
        # Thresholding
        threshold = np.max(corr_mag) * 0.2
        peaks = np.where(corr_mag > threshold)[0]
        
        if len(peaks) == 0:
            return 0.0, 0.0, corr_mag
            
        # Find the absolute max (Transmission t=0)
        max_idx = np.argmax(corr_mag)
        t0_sample = lags[max_idx]
        
        # Blank out the main peak
        # The correlation peak for a chirp is very narrow (approx 1/Bandwidth)
        # We don't need to blank the whole chirp duration, just the main lobe and immediate sidelobes.
        # Let's say 2ms safe zone approx 88 samples
        safe_zone = int(self.sample_rate * 0.002) 
        
        start_blank = max(0, max_idx - safe_zone)
        end_blank = min(len(corr_mag), max_idx + safe_zone)
        
        masked_corr = corr_mag.copy()
        masked_corr[start_blank:end_blank] = 0
        
        # Find second strongest peak (Echo)
        if np.max(masked_corr) < (np.max(corr_mag) * 0.05):
            # No significant echo found
            return 0.0, 0.0, corr_mag # No echo distance
            
        echo_idx = np.argmax(masked_corr)
        t1_sample = lags[echo_idx]
        
        # Delta
        delta_samples = t1_sample - t0_sample
        
        if delta_samples <= 0:
             return 0.0, 0.0, corr_mag
             
        distance = (delta_samples / self.sample_rate) * self.speed_of_sound / 2
        
        return distance, delta_samples, corr_mag
