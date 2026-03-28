from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bensilence",
    version="2.0.0",
    author="benimrans",
    author_email="abdullaimran997@gmail.com",
    description="A voice activity detection based audio recorder library using Silero VAD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/benimrans/bensilence",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pyaudio>=0.2.11",
        "soundfile>=0.10.0",
        "torch>=1.9.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
    ],
    python_requires=">=3.7",
    keywords="voice activity detection vad audio recording speech silero",
)