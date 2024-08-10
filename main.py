import speech_recognition as sr
import pyttsx3 as p
import time
import logging
import google.generativeai as genai
from datetime import date
import tkinter as tk
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize pyttsx3 TTS engine
engine = p.init()
engine.setProperty('rate', 190)  # Speed of speech

# Set up Google Generative AI model
api_key = "AIzaSyAMifDtuFBU7UfMmKcr6sGj2XgLhaEcPmY"  # Replace with your Google API key
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# Stop event to control the listening loop
stop_event = Event()

# Function to speak text and print it in the UI
def speak(text):
    engine.say(text)
    engine.runAndWait()
    ui(text)

# Function to log conversation
def append2log(text):
    today = str(date.today())
    fname = f'chatlog-{today}.txt'
    with open(fname, "a") as f:
        f.write(text + "\n")

# Function to listen for commands
def listen():
    rec = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        rec.adjust_for_ambient_noise(source, duration=0.1)
        ui("Listening...")
        try:
            audio = rec.listen(source, timeout=10, phrase_time_limit=5)
            text = rec.recognize_google(audio).lower()
            ui(f"Recognized Text: {text}")
            return text
        except sr.UnknownValueError:
            ui("Sorry, I did not understand that.")
            return None
        except sr.RequestError as e:
            logging.error(f"Request Error: {e}")
            return None

# Function to update the UI with new text
def ui(text):
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, text + "\n")
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)

# Function to generate AI response with timeout
def gen(request):
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(model.generate_content, request, stream=False)
            response = future.result(timeout=3)  # 3 seconds timeout
            return response.text.strip()
    except FutureTimeoutError:
        return "Sorry, the response took too long."

# Function to handle the speech-to-speech logic
def main_loop():
    while not stop_event.is_set():
        command_text = listen()
        if command_text:
            if "that's all" in command_text:
                response_text = "Bye now"
                append2log(f"AI: {response_text}\n")
                speak(response_text)
                stop_event.set()  # Stop the loop
            else:
                append2log(f"You: {command_text}\n")
                response_text = gen(command_text)
                append2log(f"AI: {response_text}\n")
                speak(response_text)
        time.sleep(1)

# Set up the Tkinter UI
def setup():
    global chat_log
    root = tk.Tk()
    root.title("Voice Assistant")

    chat_log = tk.Text(root, wrap=tk.WORD, state=tk.DISABLED)
    chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    start_button = tk.Button(root, text="Start Listening", command=start_assistant)
    start_button.pack(pady=5)

    stop_button = tk.Button(root, text="Stop Listening", command=stop_assistant)
    stop_button.pack(pady=5)

    exit_button = tk.Button(root, text="Exit", command=root.quit)
    exit_button.pack(pady=5)

    root.mainloop()

# Start the assistant in a separate thread
def start_assistant():
    stop_event.clear()
    Thread(target=main_loop).start()

# Stop the assistant
def stop_assistant():
    stop_event.set()
    speak("Assistant stopped.")

# Run the UI
setup()
