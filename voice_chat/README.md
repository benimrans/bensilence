# voice_chat

A real-time AI voice chat system built on top of **bensilence**.  
It works exactly like ChatGPT Voice: listen → transcribe → AI reply → speak, and if you talk while the AI is talking it stops immediately and listens again.

---

## Features

| Feature | Detail |
|---|---|
| **Auto-listen** | Uses bensilence (Silero VAD) — records only when you speak, stops on silence |
| **Transcription** | OpenAI Whisper |
| **AI response** | OpenAI Chat (any model — default `gpt-4o-mini`) |
| **Text-to-speech** | OpenAI TTS, streamed as raw PCM so playback starts fast |
| **Interrupt** | Separate VAD thread monitors the mic during playback; AI stops the moment speech is detected |
| **Conversation memory** | Full multi-turn history sent on every request |

---

## Requirements

- Python 3.8+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- The `bensilence` library (and its deps: `numpy`, `pyaudio`, `soundfile`, `torch`)
- `openai>=1.0.0`

Install everything from the repo root:

```bash
pip install -e .                    # installs bensilence
pip install -r voice_chat/requirements.txt   # installs openai
```

---

## Quick start

```bash
export OPENAI_API_KEY="sk-..."
python -m voice_chat.main
```

Speak.  The system transcribes your words, generates a reply, and reads it aloud.  
Speak again at any point to interrupt the AI and ask a new question.

---

## CLI options

```
usage: voice_chat [-h] [--api-key API_KEY] [--model MODEL]
                  [--voice {alloy,echo,fable,onyx,nova,shimmer}]
                  [--system SYSTEM] [--sensitivity {1,2,3}]
                  [--silence SILENCE] [--interrupt INTERRUPT]
                  [--before BEFORE] [--max-time MAX_TIME] [--debug]

options:
  --api-key      OpenAI API key (default: $OPENAI_API_KEY)
  --model        Chat model (default: gpt-4o-mini)
  --voice        TTS voice (default: alloy)
  --system       System prompt
  --sensitivity  VAD sensitivity 1-3 (default: 2)
  --silence      Silence seconds before recording stops (default: 1.0)
  --interrupt    VAD probability to trigger AI interrupt (default: 0.5)
  --before       Pre-speech buffer seconds (default: 1.0)
  --max-time     Max single-turn recording seconds (default: 60)
  --debug        Enable debug logging
```

---

## Python API

```python
from voice_chat import VoiceChat

chat = VoiceChat(
    openai_api_key="sk-...",
    model="gpt-4o",
    tts_voice="nova",
    system_prompt="You are a friendly French tutor.",
)
chat.run()   # blocks; Ctrl-C to exit
```

---

## How the interrupt works

While the AI is speaking, a lightweight **daemon thread** opens a second
microphone input stream and feeds 32 ms chunks through the same Silero VAD
model used by bensilence.  The moment speech probability exceeds
`interrupt_threshold` (default 0.5), it sets an event flag that causes the
PCM playback loop to stop on the very next audio chunk (~85 ms latency).
Control returns to the main loop which flushes the input buffer and calls
`bensilence.SilenceRecorder.record()` again from a clean state.

---

## Architecture

```
                ┌─────────────────────────────────────────────┐
                │                 VoiceChat.run()              │
                │                                             │
                │  ┌──────────┐   ┌───────────┐   ┌───────┐  │
                │  │ bensilence│──▶│  Whisper  │──▶│  GPT  │  │
                │  │  record() │   │ transcribe│   │ chat  │  │
                │  └──────────┘   └───────────┘   └───┬───┘  │
                │                                     │      │
                │          ┌──────────────────────────▼──┐   │
                │          │   _speak()  PCM playback     │   │
                │          │  ┌──────────────────────────┐│   │
                │          │  │ _interrupt_monitor thread ││   │
                │          │  │  (separate mic stream)   ││   │
                │          │  └──────────────────────────┘│   │
                │          └─────────────────────────────┘   │
                └─────────────────────────────────────────────┘
```
