# Real-Time Translation & Interview Assistant Overlay

A functional prototype of a desktop overlay application for real-time translation and interview assistance during video calls. It listens to live audio from the microphone, transcribes speech to text using OpenAI Whisper, translates it to Spanish using `gpt-4o-mini`, and provides context-aware suggested responses for interviews. All of this is displayed in a semi-transparent, always-on-top window using Tkinter.

## Requirements

- Python 3.8+
- An active OpenAI API Key

## Installation

1. Clone or download this repository.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

If you encounter issues installing `sounddevice` or `scipy`, you may need system-level audio libraries.
* On Linux (Ubuntu/Debian): `sudo apt-get install portaudio19-dev`
* On macOS: `brew install portaudio`

## Configuration

You must provide an OpenAI API key.

Create a `.env` file in the same directory as `app.py` and add your key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Alternatively, set it as an environment variable in your terminal:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

## Usage

Run the application:

```bash
python app.py
```

A semi-transparent black window will appear at the bottom of your screen. It will continuously listen to your microphone in 1-second chunks, transcribe the audio, translate it to Spanish, and display the original text, the translated text, and AI-suggested responses on the screen.

The application maintains a brief conversation history to provide relevant, context-aware suggestions, perfect for interview scenarios.

To exit, simply close the overlay window.

---

## Suggested Improvements for the Future

### 1. Real-Time Streaming Transcription
Currently, the prototype records in fixed 3-second chunks and sends them to the REST API. This introduces latency.
* **Improvement:** Move to a true streaming architecture using WebSockets or gRPC with a real-time speech-to-text provider (like Deepgram, Google Cloud Speech-to-Text streaming API, or AssemblyAI). This would allow word-by-word transcription as you speak, significantly reducing latency.

### 2. Professional Floating Overlay UI
Tkinter is lightweight but limited in styling and modern UI features.
* **Improvement:** Rewrite the UI using PyQt6/PySide6 or Electron. These frameworks allow for borderless windows, custom shapes, rich text formatting, animations, and better cross-platform compatibility. You could add features like a drag-to-move handle, opacity sliders, and language selection dropdowns.

### 3. System Audio Capture
Currently, the app only captures audio from the default microphone. During a video call, you'll also want to translate what the *other* person is saying (system audio output).
* **Improvement:** Use libraries that support loopback audio capture.
    * On Windows: WASAPI loopback (can be accessed via `soundcard` or PyAudio extensions).
    * On macOS: Using a virtual audio cable like BlackHole to route system audio into an input device.
    * On Linux: PulseAudio or PipeWire monitor devices.
    * Once captured, the app could mix microphone and system audio, or run two separate transcription threads for a "two-way" translation UI.