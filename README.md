
This is my first repsitory. So, I may not have done everything properly. I expect your understanding.

# bensilence
A voice recorder with voice activity detection (VAD). It starts recording when VAD detects speech and stops recording as the speaker stops talking for a second. Best use case would be AI assistants. This is just another version of [rhasspy-silence](https://github.com/rhasspy/rhasspy-silence). This library uses [Cobra (Picovoice)](https://picovoice.ai/platform/cobra/) for VAD, which is better than webRTC that was used in [rhasspy-silence](https://github.com/rhasspy/rhasspy-silence).



## Installation

1. Install the package:
    ``` bash
   pip install bensilence 
    ```
### Install via GitHub
1. Clone the repository:
   ``` bash
   git clone https://github.com/benimrans/bensilence.git
   cd bensilence
   ```
2. Install dependencies:
    ```bash
   pip install -r requirements.txt 
   ```
3. Setup:
    ```bash
   py setup.py install 
   ```
## Usage/Examples

You'll need a [Picovoice](https://picovoice.ai) account to get an API key. Once you get it, you are ready to go!

```python
from bensilence import silence

silence = silence(api_key="your_picovoice_api_key")

silence.initialize()

result, file_name = silence.record()

print(result, file_name)

silence.cleanup()
```

Here are some variables that you may want to change:

These are the default values.

```python
before_seconds = 1 # Adds the unrecorded parts to the recording by going back 1 second from the time the speech started.
silence_threshold = 1 # Stops recording if there's silence for 1 second. 
max_sensitivity = 2 # {1: 0.5, 2: 0.7, 3: 0.9} Value that VAD should detect to start recording.
max_recording_time = 30 # Maximum recording time.
```
## Related

This is the reason why I made this library:

[rhasspy-silence](https://github.com/rhasspy/rhasspy-silence)


## License

[MIT](https://choosealicense.com/licenses/mit/)

