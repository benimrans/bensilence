"""
bensilence - A voice activity detection based audio recorder library

This library provides functionality to record audio based on voice activity detection,
automatically starting recording when speech is detected and stopping when silence occurs.
"""

from .bensilence import SilenceRecorder, silence

__version__ = "2.0.0"
__all__ = ["SilenceRecorder", "silence"]