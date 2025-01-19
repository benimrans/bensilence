from bensilence import silence

silence = silence(api_key="your_picovoice_api_key")

silence.initialize()

result, file_name = silence.record()

print(result, file_name)
