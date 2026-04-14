#!/usr/bin/env python3
"""
main.py — Command-line entry point for the voice chat system.

Usage examples
--------------
# Simplest — reads OPENAI_API_KEY from the environment:
    python -m voice_chat.main

# Custom model and voice:
    python -m voice_chat.main --model gpt-4o --voice nova

# Custom system prompt:
    python -m voice_chat.main --system "You are a friendly French tutor."

# Adjust sensitivity / silence threshold:
    python -m voice_chat.main --sensitivity 3 --silence 1.5 --interrupt 0.4
"""

import argparse
import logging
import os
import sys


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="voice_chat",
        description="AI voice chat powered by bensilence + OpenAI.",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (default: $OPENAI_API_KEY).",
    )
    p.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Chat model (default: gpt-4o-mini).",
    )
    p.add_argument(
        "--voice",
        default="alloy",
        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        help="TTS voice (default: alloy).",
    )
    p.add_argument(
        "--system",
        default=(
            "You are a helpful voice assistant. "
            "Keep your answers concise and conversational."
        ),
        help="System prompt sent to the chat model.",
    )
    p.add_argument(
        "--sensitivity",
        type=int,
        default=2,
        choices=[1, 2, 3],
        help="VAD sensitivity 1–3 (default: 2).",
    )
    p.add_argument(
        "--silence",
        type=float,
        default=1.0,
        help="Seconds of silence before recording stops (default: 1.0).",
    )
    p.add_argument(
        "--interrupt",
        type=float,
        default=0.5,
        help=(
            "VAD probability threshold that triggers an AI interrupt "
            "(default: 0.5).  Higher = harder to interrupt."
        ),
    )
    p.add_argument(
        "--before",
        type=float,
        default=1.0,
        help="Seconds of pre-speech audio kept by bensilence (default: 1.0).",
    )
    p.add_argument(
        "--max-time",
        type=float,
        default=60.0,
        help="Maximum single-turn recording time in seconds (default: 60).",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    return p


def main() -> None:
    args = _build_parser().parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    # Resolve API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: OpenAI API key not found.\n"
            "  Set the OPENAI_API_KEY environment variable, or pass --api-key.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Import here so startup errors (missing packages, etc.) surface cleanly
    from voice_chat.voice_chat import VoiceChat

    chat = VoiceChat(
        openai_api_key=api_key,
        model=args.model,
        tts_voice=args.voice,
        system_prompt=args.system,
        before_seconds=args.before,
        max_sensitivity=args.sensitivity,
        silence_threshold=args.silence,
        interrupt_threshold=args.interrupt,
        max_recording_time=args.max_time,
    )
    chat.run()


if __name__ == "__main__":
    main()
