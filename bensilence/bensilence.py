"""
bensilence - A voice activity detection based audio recorder library

This library provides functionality to record audio based on voice activity detection,
automatically starting recording when speech is detected and stopping when silence occurs.
"""

import numpy as np
import pyaudio
import soundfile as sf
import time
from collections import deque
import logging
import torch

__version__ = "2.0.0"
__all__ = ["SilenceRecorder", "silence"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SilenceRecorder:
    """
    A voice activity detection based audio recorder.

    This class uses Silero VAD to detect speech and automatically record
    audio segments when voice is detected, stopping after a period of silence.
    """

    def __init__(self, file_name="output.wav", before_seconds=1,
                 max_sensitivity=2, max_recording_time=30, silence_threshold=1):
        """
        Initialize the SilenceRecorder.

        Args:
            file_name (str): Output filename for recorded audio
            before_seconds (float): Seconds of audio to include before speech detection
            max_sensitivity (int): Sensitivity level (1-3, higher =p easier detection)
            max_recording_time (float): Maximum recording time in seconds
            silence_threshold (float): Seconds of silence before stopping recording
        """
        self.file_name = file_name
        self.before_seconds = before_seconds
        self.silence_threshold = silence_threshold
        self.max_recording_time = max_recording_time

        self.rate = 16000
        self.chunk = 512
        self.channels = 1
        self.format = pyaudio.paInt16

        # Sensitivity: higher = easier detection
        self.sensitivity_map = {1: 0.3, 2: 0.5, 3: 0.7}
        self.sensitivity_threshold = self.sensitivity_map.get(max_sensitivity, 0.5)
        self.vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad')
        self.audio = None
        self.stream = None
        self.pre_audio_buffer = deque(maxlen=int(self.rate * self.before_seconds))

    def initialize(self):
        """Initialize PyAudio and the audio stream."""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        logging.info("PyAudio + Silero VAD initialized.")

    def pcm_to_float(self, pcm):
        """Convert PCM audio data to float format for VAD processing."""
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        return audio / 32768.0

    def save_audio(self, audio_data):
        """Save audio data to WAV file."""
        sf.write(self.file_name, np.array(audio_data, dtype=np.int16), self.rate)
        logging.info(f"Saved to {self.file_name}")

    def start_recording(self):
        """
        Start the recording process, monitoring for voice activity.

        Returns:
            tuple: (audio_frames, start_time, end_time) or (None, None, None) if timeout
        """
        recording = False
        silence_start = None
        recorded_frames = []
        continuous_frames = []

        # Initialize variables
        speech_start_time = 0
        speech_end_time = 0
        voice_detected = False

        audio_start_time = time.time()

        while True:
            frame = self.stream.read(self.chunk, exception_on_overflow=False)
            float_audio = self.pcm_to_float(frame)

            speech_prob = self.vad_model(
                torch.from_numpy(float_audio),
                self.rate
            ).item()
            continuous_frames.extend(np.frombuffer(frame, dtype=np.int16))

            now = time.time()
            elapsed = now - audio_start_time

            if speech_prob > self.sensitivity_threshold:
                if not recording:
                    logging.info("Voice detected, recording...")
                    recording = True
                    voice_detected = True
                    recorded_frames.extend(self.pre_audio_buffer)
                    speech_start_time = elapsed

                recorded_frames.extend(np.frombuffer(frame, dtype=np.int16))
                silence_start = None

            elif recording:
                if silence_start is None:
                    silence_start = now
                elif now - silence_start > self.silence_threshold:
                    speech_end_time = elapsed
                    logging.info("Silence detected, stopping.")
                    break

            self.pre_audio_buffer.extend(np.frombuffer(frame, dtype=np.int16))

            # Check for timeout
            if elapsed >= self.max_recording_time:
                speech_end_time = elapsed
                logging.info("Recording period ended.")
                break

        # If no voice detected, return None
        if not voice_detected:
            return None, None, None

        return continuous_frames, max(0, speech_start_time - self.before_seconds), speech_end_time

    def record(self):
        """
        Main recording method that waits for voice and saves the audio.

        Returns:
            tuple: ("Successful", filename) or ("Timeout", None)
        """
        logging.info("Waiting for voice...")
        audio, start, end = self.start_recording()

        if audio is None:
            return "Timeout", None

        final_audio = audio[int(start * self.rate):int(end * self.rate)]
        self.save_audio(final_audio)
        return "Successful", self.file_name

    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        logging.info("Cleaned up.")

def silence(file_name="output.wav", **kwargs):
    """
    Factory function to create a SilenceRecorder instance.

    Args:
        file_name (str): Output filename
        **kwargs: Additional arguments passed to SilenceRecorder.__init__

    Returns:
        SilenceRecorder: Configured recorder instance
    """
    recorder = SilenceRecorder(file_name, **kwargs)
    return recorder