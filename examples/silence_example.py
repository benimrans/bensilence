from bensilence import silence

result, file_name = silence(api_key="your_picovoice_api_key", file_name="output.wav")

print(result, file_name)