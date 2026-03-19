import os
import queue
import threading
import time
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from openai import OpenAI
import tkinter as tk
from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY from .env)
load_dotenv()

# Configuration
SAMPLE_RATE = 16000  # 16kHz is optimal for Whisper
CHUNK_DURATION = 3   # 3 seconds per audio chunk
CHANNELS = 1         # Mono audio

# Initialize OpenAI Client
# Make sure to set the OPENAI_API_KEY environment variable.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Thread-safe queues for inter-thread communication
audio_queue = queue.Queue()
text_queue = queue.Queue()

# Global flag to control loops
is_running = True

def record_audio():
    """
    Continuously records audio from the microphone in chunks and adds them to a queue.
    """
    print("Started recording audio...")
    try:
        while is_running:
            # Record audio for CHUNK_DURATION seconds
            recording = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE),
                               samplerate=SAMPLE_RATE,
                               channels=CHANNELS,
                               dtype='int16')
            sd.wait()  # Block until the recording chunk finishes

            # Put the recorded chunk into the queue
            if is_running:
                audio_queue.put(recording)
    except Exception as e:
        print(f"Error recording audio: {e}")

def transcribe_audio(audio_data):
    """
    Transcribes the audio chunk using OpenAI's Whisper API.
    """
    try:
        # Save audio chunk to a temporary WAV file for the API
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_filename = temp_wav.name

        wav.write(temp_filename, SAMPLE_RATE, audio_data)

        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                # prompt="The following is a conversational speech." # Optional context
            )

        # Clean up the temporary file
        os.remove(temp_filename)
        return transcript.text.strip()
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""

def translate_text(text):
    """
    Translates the transcribed text into Spanish using OpenAI's GPT model.
    """
    if not text:
        return ""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # GPT-3.5 is fast and cost-effective; GPT-4 can be used for better accuracy
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled real-time translator. Translate the following text to Spanish. "
                               "If it is already in Spanish, refine it or output as is. Output ONLY the translation without any extra comments."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3 # Lower temperature for more accurate/deterministic translations
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error translating text: {e}")
        return ""

def process_pipeline():
    """
    Pull audio chunks from the queue, transcribe them, translate them, and send to the UI queue.
    """
    print("Started processing pipeline...")
    while is_running:
        try:
            # Fetch an audio chunk with a timeout to keep checking the `is_running` flag
            audio_data = audio_queue.get(timeout=1)

            # 1. Transcribe the audio chunk
            original_text = transcribe_audio(audio_data)

            # Ignore empty transcriptions (e.g., silence)
            if not original_text:
                continue

            # 2. Translate the text to Spanish
            translated_text = translate_text(original_text)

            # 3. Queue the texts for the UI to display
            text_queue.put((original_text, translated_text))

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in processing pipeline: {e}")

def update_ui(root, original_label, translated_label):
    """
    Continuously updates the Tkinter UI with new transcriptions and translations.
    """
    try:
        # Process all available text updates in the queue
        while not text_queue.empty():
            original_text, translated_text = text_queue.get_nowait()

            # Update the overlay labels
            original_label.config(text=f"Original: {original_text}")
            translated_label.config(text=f"Translated: {translated_text}")

    except Exception as e:
        print(f"Error updating UI: {e}")

    # Schedule the next UI update check in 100 milliseconds
    if is_running:
        root.after(100, update_ui, root, original_label, translated_label)

def on_closing(root):
    """
    Cleanly shuts down the application when the window is closed.
    """
    global is_running
    is_running = False
    print("Shutting down application...")
    root.destroy()

def create_gui():
    """
    Initializes and configures the Tkinter floating overlay window.
    """
    root = tk.Tk()
    root.title("Real-Time Translator Overlay")

    # Configure the window to be a floating overlay
    root.attributes('-topmost', True) # Keep the window on top of others
    root.attributes('-alpha', 0.85)   # Make the window semi-transparent

    # Window dimensions and positioning
    window_width = 700
    window_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Position at the center-bottom of the screen
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int(screen_height - window_height - 80)
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    # Basic styling
    root.configure(bg='black')

    # Label for original text
    original_label = tk.Label(root, text="Listening for speech...",
                              font=("Helvetica", 11), fg="lightgray", bg="black",
                              wraplength=680, justify="center")
    original_label.pack(pady=10)

    # Label for translated text
    translated_label = tk.Label(root, text="Translation will appear here...",
                                font=("Helvetica", 14, "bold"), fg="#FFD700", bg="black",
                                wraplength=680, justify="center")
    translated_label.pack(pady=10)

    # Handle the window close event gracefully
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))

    # Start the UI update loop
    root.after(100, update_ui, root, original_label, translated_label)

    return root

def main():
    # Verify OpenAI API Key is present
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your environment or add it to a .env file.")
        return

    # 1. Start the audio recording thread
    record_thread = threading.Thread(target=record_audio, daemon=True)
    record_thread.start()

    # 2. Start the processing (transcription & translation) thread
    process_thread = threading.Thread(target=process_pipeline, daemon=True)
    process_thread.start()

    # 3. Start the Tkinter GUI event loop (Must run on the main thread)
    root = create_gui()
    root.mainloop()

if __name__ == "__main__":
    main()
