"""
voice_chat.py — Core VoiceChat class.

Flow per turn:
  1. Listen  : bensilence records the user utterance (VAD-triggered).
  2. Transcribe : OpenAI Whisper converts the WAV to text.
  3. Think   : OpenAI Chat generates a reply.
  4. Speak   : OpenAI TTS streams raw PCM audio to the speakers.
               A lightweight interrupt-monitor thread watches the microphone
               using the same Silero VAD model; if speech is detected while
               the AI is talking, playback stops immediately and the loop
               goes straight back to step 1 — exactly like ChatGPT Voice.
"""

import logging
import os
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import pyaudio
import torch

from bensilence import SilenceRecorder

logger = logging.getLogger(__name__)


class VoiceChat:
    """
    A voice chat system that uses bensilence for VAD-based recording,
    sends audio to an AI, speaks the response, and supports real-time
    interrupt detection so the user can cut the AI off mid-sentence.

    Parameters
    ----------
    openai_api_key : str, optional
        OpenAI API key.  Falls back to the OPENAI_API_KEY environment variable.
    model : str
        Chat model to use (default: "gpt-4o-mini").
    tts_voice : str
        OpenAI TTS voice (alloy | echo | fable | onyx | nova | shimmer).
    system_prompt : str
        System message sent to the chat model on every conversation.
    before_seconds : float
        Seconds of pre-speech audio included by bensilence (default: 1).
    max_sensitivity : int
        bensilence sensitivity level 1–3 (default: 2).
    silence_threshold : float
        Seconds of silence before bensilence stops recording (default: 1.0).
    interrupt_threshold : float
        Silero VAD probability (0–1) that triggers an interrupt while the AI
        is speaking (default: 0.5).  Raise to reduce false positives.
    max_recording_time : float
        Maximum single-turn recording length in seconds (default: 60).
    """

    # OpenAI TTS PCM output: 24 kHz, 16-bit, mono
    _TTS_RATE = 24_000
    # VAD chunk size used by bensilence (and our interrupt monitor)
    _VAD_CHUNK = 512
    _VAD_RATE = 16_000

    def __init__(
        self,
        openai_api_key: str = None,
        model: str = "gpt-4o-mini",
        tts_voice: str = "alloy",
        system_prompt: str = (
            "You are a helpful voice assistant. "
            "Keep your answers concise and conversational."
        ),
        before_seconds: float = 1.0,
        max_sensitivity: int = 2,
        silence_threshold: float = 1.0,
        interrupt_threshold: float = 0.5,
        max_recording_time: float = 60.0,
    ):
        # Lazy-import openai so the rest of the module works without it
        try:
            import openai as _openai
        except ImportError as exc:
            raise ImportError(
                "openai package is required: pip install openai"
            ) from exc

        api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "An OpenAI API key is required.  "
                "Pass it as openai_api_key= or set the OPENAI_API_KEY "
                "environment variable."
            )
        self._client = _openai.OpenAI(api_key=api_key)

        self.model = model
        self.tts_voice = tts_voice
        self.interrupt_threshold = interrupt_threshold

        # Conversation history (grows with each turn)
        self._history = [{"role": "system", "content": system_prompt}]

        # bensilence recorder — we reuse its PyAudio instance and VAD model
        self._tmp_wav = str(Path(tempfile.gettempdir()) / "voice_chat_input.wav")
        self._recorder = SilenceRecorder(
            file_name=self._tmp_wav,
            before_seconds=before_seconds,
            max_sensitivity=max_sensitivity,
            max_recording_time=max_recording_time,
            silence_threshold=silence_threshold,
        )
        # Silero VAD model shared from the recorder (already loaded)
        self._vad = self._recorder.vad_model

        # PyAudio instance — set after initialize()
        self._pa: pyaudio.PyAudio = None

        # Interrupt signalling
        self._interrupt = threading.Event()
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Open audio streams.  Must be called before :meth:`run`."""
        self._recorder.initialize()
        # Reuse the PyAudio instance that bensilence already created
        self._pa = self._recorder.audio
        logger.info("VoiceChat initialised (model=%s, voice=%s).", self.model, self.tts_voice)

    def cleanup(self) -> None:
        """Release all audio resources."""
        self._stop.set()
        self._recorder.cleanup()
        logger.info("VoiceChat cleaned up.")

    # ------------------------------------------------------------------
    # Public conversation control
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Start the voice chat loop.

        Blocks until Ctrl-C is pressed or :meth:`cleanup` is called from
        another thread.
        """
        print("\n=== Voice Chat ===")
        print(f"  model : {self.model}")
        print(f"  voice : {self.tts_voice}")
        print("Speak to start.  Press Ctrl-C to exit.\n")

        self.initialize()

        try:
            while not self._stop.is_set():
                self._one_turn()
        except KeyboardInterrupt:
            print("\nExiting voice chat.")
        finally:
            self.cleanup()

    # ------------------------------------------------------------------
    # Internal: single conversation turn
    # ------------------------------------------------------------------

    def _one_turn(self) -> None:
        """Listen → transcribe → think → speak (with interrupt support)."""
        # ── 1. Listen ──────────────────────────────────────────────────
        print("🎤  Listening…")
        self._flush_recorder_stream()
        result, filename = self._recorder.record()

        if result != "Successful" or not filename:
            logger.debug("No speech detected, looping.")
            return

        # ── 2. Transcribe ──────────────────────────────────────────────
        print("💭  Transcribing…")
        try:
            user_text = self._transcribe(filename)
        except Exception as exc:
            logger.error("Transcription failed: %s", exc)
            return

        if not user_text:
            return

        print(f"You: {user_text}")

        # ── 3. Get AI response ─────────────────────────────────────────
        print("🤖  Thinking…")
        try:
            reply = self._chat(user_text)
        except Exception as exc:
            logger.error("Chat completion failed: %s", exc)
            return

        print(f"AI:  {reply}")

        # ── 4. Speak (stops early on interrupt) ────────────────────────
        print("🔊  Speaking…")
        completed = self._speak(reply)

        if not completed:
            print("(Interrupted — listening again…)")

    # ------------------------------------------------------------------
    # Internal: audio helpers
    # ------------------------------------------------------------------

    def _flush_recorder_stream(self) -> None:
        """
        Close and reopen the bensilence input stream to discard any audio
        that accumulated in the ring buffer while the AI was speaking.
        This prevents stale frames from polluting the next recording.
        """
        r = self._recorder
        try:
            if r.stream and r.stream.is_active():
                r.stream.stop_stream()
            r.stream.close()
        except Exception:
            pass
        r.stream = r.audio.open(
            format=r.format,
            channels=r.channels,
            rate=r.rate,
            input=True,
            frames_per_buffer=r.chunk,
        )
        r.pre_audio_buffer.clear()

    def _transcribe(self, wav_path: str) -> str:
        """Call OpenAI Whisper and return the transcript text."""
        with open(wav_path, "rb") as fh:
            resp = self._client.audio.transcriptions.create(
                model="whisper-1",
                file=fh,
            )
        return resp.text.strip()

    def _chat(self, user_text: str) -> str:
        """Append user message, call the chat model, append AI reply."""
        self._history.append({"role": "user", "content": user_text})
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=self._history,
        )
        reply = resp.choices[0].message.content.strip()
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def _tts_pcm(self, text: str) -> bytes:
        """
        Generate speech with OpenAI TTS.

        Returns raw 24 kHz / 16-bit / mono PCM bytes so we can feed them
        directly into a PyAudio output stream.
        """
        resp = self._client.audio.speech.create(
            model="tts-1",
            voice=self.tts_voice,
            input=text,
            response_format="pcm",
        )
        return resp.content

    # ------------------------------------------------------------------
    # Internal: interrupt monitor
    # ------------------------------------------------------------------

    def _interrupt_monitor(self) -> None:
        """
        Runs in a daemon thread while the AI is speaking.

        Opens a *separate* input stream (PyAudio supports multiple
        simultaneous streams from the same device), continuously feeds
        mic chunks through Silero VAD, and sets self._interrupt as soon
        as speech is detected.
        """
        try:
            stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._VAD_RATE,
                input=True,
                frames_per_buffer=self._VAD_CHUNK,
            )
        except Exception as exc:
            logger.warning("Could not open interrupt-monitor stream: %s", exc)
            return

        logger.debug("Interrupt monitor started.")
        try:
            while not self._interrupt.is_set() and not self._stop.is_set():
                try:
                    raw = stream.read(self._VAD_CHUNK, exception_on_overflow=False)
                except OSError:
                    break
                floats = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                prob = self._vad(
                    torch.from_numpy(floats),
                    self._VAD_RATE,
                ).item()
                if prob > self.interrupt_threshold:
                    logger.info("User speech detected — interrupting AI.")
                    self._interrupt.set()
                    break
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            logger.debug("Interrupt monitor stopped.")

    # ------------------------------------------------------------------
    # Internal: TTS playback with interrupt support
    # ------------------------------------------------------------------

    def _speak(self, text: str) -> bool:
        """
        Generate TTS audio and play it, while monitoring the microphone.

        Returns
        -------
        bool
            True  — playback finished naturally.
            False — playback was cut short by a user interruption.
        """
        try:
            pcm = self._tts_pcm(text)
        except Exception as exc:
            logger.error("TTS generation failed: %s", exc)
            return True  # Nothing to play; treat as completed

        # Clear any previous interrupt signal
        self._interrupt.clear()

        # Start the interrupt monitor
        monitor = threading.Thread(target=self._interrupt_monitor, daemon=True)
        monitor.start()

        # Open PCM output stream at the TTS sample rate
        out = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._TTS_RATE,
            output=True,
        )

        _CHUNK = 4096  # bytes per write (~85 ms at 24 kHz / 16-bit / mono)
        interrupted = False
        try:
            for offset in range(0, len(pcm), _CHUNK):
                if self._interrupt.is_set():
                    interrupted = True
                    break
                out.write(pcm[offset : offset + _CHUNK])
        finally:
            try:
                out.stop_stream()
                out.close()
            except Exception:
                pass
            # Signal the monitor to exit (it may already have)
            self._interrupt.set()
            monitor.join(timeout=2.0)

        return not interrupted
