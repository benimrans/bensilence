from setuptools import setup, find_packages

setup(
    name="bensilence",  # Your library name
    version="0.1.2",  # Initial version
    author="Imran (benimrans)",  # Your name
    author_email="abdullaimran997@example.com",  # Your email
    description="A Python library for recording voice using voice actvity detection (VAD). Best for AI voice assistants.",
    long_description=open("README.md").read(),  # Contents of your README file
    long_description_content_type="text/markdown",  # README format
    url="https://github.com/benimrans/bensilence",  # URL to your GitHub repo
    packages=find_packages(),  # Automatically find packages in your project
    install_requires=[
        "numpy",
        "pyaudio",
        "pvcobra",
        "soundfile",
    ],  # Dependencies
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Minimum Python version
)
