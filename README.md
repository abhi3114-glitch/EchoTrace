# EchoTrace

EchoTrace is a Python-based sonar distance visualizer that utilizes a laptop's built-in speakers and microphone to measure distance to nearby objects using active sonar techniques. It emits linear chirp signals (2kHz - 8kHz), listens for the echo, and calculates the time-of-flight to estimate distance.

## Features

- **Active Sonar Emission**: Generates and plays periodic linear frequency modulated (LFM) chirps.
- **Microphone Echo Detection**: Continuously records audio and performs cross-correlation to detect signal reflections.
- **Real-time Visualization**: Displays the raw correlation signal and a historical distance trend graph using Matplotlib and Tkinter.
- **Data Export**: Allows saving distance logs to CSV and capturing the current visualization as a PNG image.
- **Local Processing**: All signal processing runs locally on the CPU using NumPy and SciPy.

## Tech Stack

- **Python 3.11+**
- **SoundDevice/PyAudio**: For low-latency audio input/output.
- **NumPy & SciPy**: For signal generation (chirps) and processing (correlation, peak detection).
- **Matplotlib**: For real-time data plotting.
- **Tkinter**: For the graphical user interface.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/abhi3114-glitch/EchoTrace.git
   cd EchoTrace
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Linux, you may need to install `python3-tk` and `portaudio` development headers separately.*

## Usage

1. Run the main application:
   ```bash
   python main.py
   ```

2. Click the **Start Sonar** button in the UI. You will hear a rapid ticking or chirping sound from your speakers.

3. Move a flat object (like a hand or a book) in front of the laptop. The system works best when the object is moving slowly within 0.5 to 1.5 meters.

4. The **Distance Trend** graph will plot the estimated distance over time. The **Correlation Signal** graph shows the raw echo strength processing.

5. Use **Export CSV** to save the session data or **Save Snapshot** to save an image of the current graph.

## How It Works

1. **Emission**: The system generates a 5ms chirp signal sweeping from 2kHz to 8kHz.
2. **Loopback & Calibration**: The microphone picks up the direct sound from the speakers (loudest peak) and sets this as time-zero (t=0).
3. **Echo Detection**: It looks for secondary peaks in the cross-correlation of the recorded audio against the reference chirp.
4. **Distance Calculation**: The time delay (dt) between the direct path and the echo is converted to distance: `Distance = (dt * SpeedOfSound) / 2`.

## Troubleshooting

- **No Signal**: Ensure your microphone volume is high and the correct device is selected as default in your OS sound settings.
- **Constant Distance**: If the graph is flat, the system might be detecting a static reflection or the direct signal alias. Try increasing the volume or moving the object closer/farther to disrupt the standing wave.
- **Audio Feedback**: If you hear a loud squeal, turn down the volume slightly or reposition the laptop.

## License

This project is open-source and available under the MIT License.
