import numpy as np
import pyaudio
import pvcobra
import soundfile as sf
import time
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SilenceRecorder:
    def __init__(self, api_key, file_name="output.wav", before_seconds=1, 
                 max_sensitivity=2, max_recording_time=30, silence_threshold=1):
        self.api_key = api_key
        self.file_name = file_name
        self.before_seconds = before_seconds
        self.silence_threshold = silence_threshold
        self.max_sensitivity = max_sensitivity
        self.max_recording_time = max_recording_time

        # Derived values
        self.rate = 16000  # Sample rate
        self.chunk = 512  # Frames per buffer
        self.channels = 1
        self.format = pyaudio.paInt16
        self.sensitivity_map = {1: 0.5, 2: 0.7, 3: 0.9}
        self.sensitivity_threshold = self.sensitivity_map.get(self.max_sensitivity, 0.9)

        self.cobra = None
        self.stream = None
        self.audio = None
        self.pre_audio_buffer = deque(maxlen=int(self.rate * self.before_seconds))

    def initialize(self):
        """Initialize PyAudio and Cobra VAD."""
        try:
            self.cobra = pvcobra.create(access_key=self.api_key)
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(format=self.format, channels=self.channels, 
                                        rate=self.rate, input=True, frames_per_buffer=self.chunk)
            logging.info("PyAudio and Cobra initialized.")
        except Exception as e:
            logging.error(f"Error: {e}")
            return "Error", None
    def pcm_to_numpy(self, pcm_data):
        """Convert PCM data to numpy array."""
        return np.frombuffer(pcm_data, dtype=np.int16)

    def cut_audio(self, continuous_audio, start_time, end_time):
        """Cut the continuous audio from start_time to end_time."""
        start_frame = int(max(0, start_time) * self.rate)
        end_frame = int(end_time * self.rate)
        return continuous_audio[start_frame:end_frame]

    def save_audio(self, audio_data):
        """Save the recorded audio to a WAV file."""
        logging.info(f"Saving recording to {self.file_name}")
        audio_array = np.array(audio_data, dtype=np.int16)
        sf.write(self.file_name, audio_array, self.rate)

    def start_recording(self):
        """Record audio and handle VAD detection."""
        recording = False
        silence_start = None
        recorded_frames = []
        continuous_frames = []
        audio_start_time = time.time()

        while True:
            frame = self.stream.read(self.chunk, exception_on_overflow=False)
            audio_frame = self.pcm_to_numpy(frame)
            vad_probability = self.cobra.process(audio_frame)
            continuous_frames.extend(audio_frame)

            current_time = time.time()
            elapsed_time = current_time - audio_start_time

            if vad_probability > self.sensitivity_threshold:
                if not recording:
                    logging.info("Voice detected, starting recording...")
                    recording = True
                    recorded_frames.extend(self.pre_audio_buffer)

                    speech_start_time = current_time - audio_start_time
                    start_record_time = max(0, speech_start_time)
                recorded_frames.extend(audio_frame)
                silence_start = None
            else:
                if recording:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > self.silence_threshold:
                        speech_end_time = current_time - audio_start_time 
                        logging.info("Silence detected, stopping recording...")
                        break

            self.pre_audio_buffer.extend(audio_frame)

            if elapsed_time >= self.max_recording_time:
                logging.info("Max recording time reached, stopping...")
                break

        return continuous_frames, speech_start_time - self.before_seconds, speech_end_time

    def record(self):
        """Perform voice activity detection and save recording."""
        try:
            logging.info("Waiting for voice activity...")
            continuous_audio, start_time, end_time = self.start_recording()
            if start_time is not None and end_time is not None:
                logging.info(f"Cutting audio from {start_time:.2f}s to {end_time:.2f}s")
                final_audio = self.cut_audio(continuous_audio, start_time, end_time)
                self.save_audio(final_audio)
            return "Successful", self.file_name
        except Exception as e:
            logging.error(f"Error: {e}")
            return "Error", None
            self.cleanup()
    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        if self.cobra:
            self.cobra.delete()
        logging.info("Resources cleaned up.")


def silence(api_key, file_name="output.wav", before_seconds=1, 
            max_sensitivity=2, max_recording_time=30, silence_threshold=1):
    recorder = SilenceRecorder(api_key, file_name, before_seconds, 
                               max_sensitivity, max_recording_time, silence_threshold)
    return recorder
