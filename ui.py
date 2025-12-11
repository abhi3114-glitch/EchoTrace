import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
import csv
from datetime import datetime

from audio_engine import AudioEngine
from processor import SignalProcessor

class EchoTraceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EchoTrace - Laptop Sonar")
        self.geometry("1000x700")
        
        # Audio & Proc
        self.audio = AudioEngine()
        self.processor = SignalProcessor(self.audio.sample_rate)
        
        # State
        self.is_running = False
        self.distance_history = []
        self.max_history = 100
        self.accumulated_audio = np.zeros(0)
        self.period_samples = int(self.audio.sample_rate * self.audio.interval)
        
        self.init_ui()
        
    def init_ui(self):
        # Top Control Panel
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_start = ttk.Button(control_frame, text="Start Sonar", command=self.toggle_sonar)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        btn_export = ttk.Button(control_frame, text="Export CSV", command=self.export_csv)
        btn_export.pack(side=tk.LEFT, padx=5)

        btn_snap = ttk.Button(control_frame, text="Save Snapshot", command=self.save_snapshot)
        btn_snap.pack(side=tk.LEFT, padx=5)
        
        # Status Label
        self.lbl_status = ttk.Label(control_frame, text="Status: Ready", font=("Arial", 12))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)
        
        self.lbl_distance = ttk.Label(control_frame, text="Distance: --- cm", font=("Arial", 16, "bold"))
        self.lbl_distance.pack(side=tk.RIGHT, padx=20)

        # Graphs Area
        graph_frame = ttk.Frame(self)
        graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Matplotlib Setup
        self.fig, (self.ax_signal, self.ax_dist) = plt.subplots(2, 1, figsize=(8, 6))
        self.fig.tight_layout(pad=3.0)
        
        self.ax_signal.set_title("Correlation Signal (Echo Detection)")
        self.ax_signal.set_xlabel("Lag (Samples)")
        self.ax_signal.set_ylabel("Amplitude")
        
        self.ax_dist.set_title("Distance Trend")
        self.ax_dist.set_xlabel("Time (frames)")
        self.ax_dist.set_ylabel("Distance (m)")
        self.ax_dist.set_ylim(0, 2.0) # Assume close range < 2m
        
        self.line_corr, = self.ax_signal.plot([], [], color='cyan', lw=1)
        self.line_dist, = self.ax_dist.plot([], [], color='lime', lw=2)
        
        # Style
        self.fig.patch.set_facecolor('#1e1e1e')
        for ax in [self.ax_signal, self.ax_dist]:
            ax.set_facecolor('#2e2e2e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.grid(True, color='#444444')
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Start update loop
        self.update_loop()

    def toggle_sonar(self):
        if self.is_running:
            self.audio.stop()
            self.btn_start.config(text="Start Sonar")
            self.lbl_status.config(text="Status: Stopped")
            self.is_running = False
        else:
            self.audio.start()
            self.btn_start.config(text="Stop Sonar")
            self.lbl_status.config(text="Status: Running")
            self.is_running = True
            
    def update_loop(self):
        if self.is_running:
            # Fetch data from queue
            try:
                # Get all available blocks
                while not self.audio.audio_queue.empty():
                    block = self.audio.audio_queue.get_nowait()
                    self.accumulated_audio = np.concatenate((self.accumulated_audio, block.flatten()))
                
                # If we have enough for a period (plus a bit for safety)
                # We process one period at a time
                if len(self.accumulated_audio) >= self.period_samples:
                    # Take the standard period size
                    chunk = self.accumulated_audio[:self.period_samples]
                    
                    # Keep the rest, but handle overflow if processing is slow
                    # Just keep the last bit to overlap? 
                    # Simpler: Just slide window. 
                    # For now, distinct chunks:
                    self.accumulated_audio = self.accumulated_audio[self.period_samples:]
                    
                    # Process
                    dist, samples, corr = self.processor.find_echo_distance(chunk, self.audio.chirp_signal)
                    
                    # Update Visuals
                    # Downsample correlation for speed
                    display_corr = corr[::10] 
                    self.line_corr.set_ydata(display_corr)
                    self.line_corr.set_xdata(np.arange(len(display_corr)) * 10)
                    self.ax_signal.set_xlim(0, len(corr))
                    self.ax_signal.set_ylim(0, np.max(corr) * 1.1 + 0.1)
                    
                    # Update Distance
                    if dist > 0:
                        self.distance_history.append(dist)
                        self.lbl_distance.config(text=f"Distance: {dist*100:.1f} cm")
                    else:
                        # Append None or last value?
                        self.distance_history.append(self.distance_history[-1] if self.distance_history else 0)
                        self.lbl_distance.config(text=f"Distance: --")
                    
                    if len(self.distance_history) > self.max_history:
                        self.distance_history.pop(0)
                        
                    self.line_dist.set_data(range(len(self.distance_history)), self.distance_history)
                    self.ax_dist.set_xlim(0, self.max_history)
                    
                    self.canvas.draw_idle()
                    
            except Exception as e:
                print(f"Error in update loop: {e}")
        
        self.after(50, self.update_loop) # Check every 50ms

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv")
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Distance_m"])
                # We assume 100ms interval for timestamps roughly
                now = datetime.now()
                for i, d in enumerate(self.distance_history):
                    writer.writerow([now, d])

    def save_snapshot(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png")
        if filename:
            self.fig.savefig(filename)

if __name__ == "__main__":
    app = EchoTraceApp()
    app.mainloop()
