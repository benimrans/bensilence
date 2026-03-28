#!/usr/bin/env python3
"""
Example usage of the bensilence library.

This script demonstrates how to use the SilenceRecorder class
to record audio based on voice activity detection.
"""

from bensilence import SilenceRecorder

def main():
    # Create a recorder with custom settings
    recorder = SilenceRecorder(
        file_name="example_recording.wav",
        before_seconds=1,      # Include 1 second before speech
        max_sensitivity=2,     # Medium sensitivity
        max_recording_time=30, # Max 30 seconds
        silence_threshold=1    # Stop after 1 second of silence
    )

    print("Initializing audio...")
    recorder.initialize()

    print("Waiting for voice activity... (speak to start recording)")
    result, filename = recorder.record()

    if result == "Successful":
        print(f"Recording saved to: {filename}")
    elif result == "Timeout":
        print("No voice detected within the time limit")
    else:
        print(f"Recording failed: {result}")

    recorder.cleanup()
    print("Done!")

if __name__ == "__main__":
    main()