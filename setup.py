from setuptools import setup, find_packages

setup(
    name="bensilence",
    version="0.1.3",
    author="Imran (benimrans)",
    author_email="abdullaimran997@example.com",
    description="A Python library for recording voice using voice actvity detection (VAD). Best for AI voice assistants.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/benimrans/bensilence",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pyaudio",
        "pvcobra",
        "soundfile",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
