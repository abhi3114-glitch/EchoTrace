import numpy as np
import sounddevice as sd
from scipy.signal import chirp
import threading
import queue

class AudioEngine:
    def __init__(self, sample_rate=44100, block_size=4096):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.stream = None
        self.running = False
        self.audio_queue = queue.Queue(maxsize=10) # Store recorded blocks
        
        # Default Chirp Parameters
        self.f0 = 2000
        self.f1 = 8000
        self.duration = 0.005 # 5ms chirp
        self.interval = 0.1 # 100ms interval between chirps
        
        self.generate_signal()
        
    def generate_signal(self):
        """Generates the chirp signal repeated to fill a buffer or just the single chirp."""
        # Total samples for one period (silence + chirp)
        period_samples = int(self.sample_rate * self.interval)
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
        self.chirp_signal = chirp(t, f0=self.f0, f1=self.f1, t1=self.duration, method='linear')
        
        # Apply window to avoid clicking
        window = np.hanning(len(self.chirp_signal))
        self.chirp_signal = self.chirp_signal * window
        
        # Create a full buffer with the chirp at the start and silence for the rest
        self.output_buffer = np.zeros(period_samples)
        self.output_buffer[:len(self.chirp_signal)] = self.chirp_signal
        
        # We need an index to track playback position if block_size != period_samples
        self.play_idx = 0
        
    def set_frequencies(self, f0, f1):
        self.f0 = f0
        self.f1 = f1
        self.generate_signal()

    def start(self):
        if self.running:
            return
            
        self.running = True
        self.play_idx = 0
        try:
            self.stream = sd.Stream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            self.stream.start()
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            self.running = False

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def audio_callback(self, indata, outdata, frames, time, status):
        """
        Callback for sounddevice. 
        We write the chirp to outdata and read mic input from indata.
        """
        if status:
            print(status)
            
        # --- PLAYBACK LOGIC ---
        # Write from our circular output_buffer
        # We might need to wrap around ifframes > remaining buffer
        
        remaining = len(self.output_buffer) - self.play_idx
        
        if remaining >= frames:
            # Easy case, just copy
            outdata[:, 0] = self.output_buffer[self.play_idx : self.play_idx + frames]
            self.play_idx += frames
        else:
            # Wrap around
            outdata[:remaining, 0] = self.output_buffer[self.play_idx:]
            outdata[remaining:, 0] = self.output_buffer[:frames - remaining]
            self.play_idx = frames - remaining
            
        # If we reached the end of the buffer, loop back
        # Ideally period_samples is a multiple of block_size, but if not we handle it above.
        if self.play_idx >= len(self.output_buffer):
            self.play_idx %= len(self.output_buffer)

        # --- RECORDING LOGIC ---
        # Put the recorded data into a queue for the processor
        if self.running:
            # Copy to avoid race conditions if indata is reused
            try:
                self.audio_queue.put_nowait(indata.copy())
            except queue.Full:
                pass # Drop frames if processing is too slow
