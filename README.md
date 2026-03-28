# bensilence

A voice activity detection (VAD) based audio recorder library. It automatically starts recording when speech is detected and stops when silence occurs. Perfect for AI assistants and voice applications.

This library uses [Silero VAD](https://github.com/snakers4/silero-models) for voice activity detection, providing high-quality speech detection without requiring API keys.

## Features

- **Voice Activity Detection**: Uses Silero VAD for accurate speech detection
- **Pre-buffering**: Capture audio from before speech detection starts
- **Configurable Sensitivity**: Adjust detection sensitivity (1-3 levels)
- **Silence Threshold**: Customizable silence duration before stopping
- **Time Limits**: Maximum recording time protection
- **Easy Integration**: Simple API for quick implementation

## Installation

### Install from source
1. Clone or download this repository
2. Navigate to the bensilence folder
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the package:
   ```bash
   pip install .
   ```

## Usage

### Basic Usage

```python
from bensilence import SilenceRecorder

# Create recorder
recorder = SilenceRecorder(file_name="my_recording.wav")
recorder.initialize()

# Start recording (waits for voice, records until silence)
result, filename = recorder.record()

print(f"Recording result: {result}")
if filename:
    print(f"Saved to: {filename}")

# Clean up
recorder.cleanup()
```

### Advanced Usage

```python
from bensilence import silence

# Create recorder with custom settings
recorder = silence(
    file_name="output.wav",
    before_seconds=2,        # Include 2 seconds before speech starts
    max_sensitivity=2,       # Medium sensitivity
    max_recording_time=60,   # Max 60 seconds
    silence_threshold=1.5    # Stop after 1.5 seconds of silence
)

recorder.initialize()
result, filename = recorder.record()
recorder.cleanup()
```

### Configuration Parameters

- `file_name`: Output filename (default: "output.wav")
- `before_seconds`: Seconds of audio to include before speech detection (default: 0)
- `max_sensitivity`: Detection sensitivity 1-3 (default: 2)
  - 1: Less sensitive (0.3 threshold)
  - 2: Medium sensitivity (0.5 threshold)
  - 3: More sensitive (0.7 threshold)
- `max_recording_time`: Maximum recording duration in seconds (default: 30)
- `silence_threshold`: Seconds of silence before stopping (default: 1)

## Dependencies

- numpy: For audio data processing
- pyaudio: For audio input/output
- soundfile: For WAV file handling
- torch: For Silero VAD model

## License

MIT License - see LICENSE file for details

## Related Projects

- [Original bensilence](https://github.com/benimrans/bensilence) - Uses Picovoice Cobra VAD
- [rhasspy-silence](https://github.com/rhasspy/rhasspy-silence) - WebRTC-based VAD