"""
voice_chat - A voice chat system built on bensilence.

Automatically listens for speech, transcribes it, queries an AI,
and speaks the response — stopping immediately if the user interrupts.
"""

from .voice_chat import VoiceChat

__version__ = "1.0.0"
__all__ = ["VoiceChat"]
