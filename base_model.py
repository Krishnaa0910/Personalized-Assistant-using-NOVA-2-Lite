import requests
import speech_recognition as sr
import pyttsx3
import datetime
import os
import wikipedia
import subprocess
import time
import platform
from plyer import notification
import logging

# Optional: Import pyautogui if supported
try:
    import pyautogui
    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------- DeepSeek via OpenRouter --------------------
import openai
openai.api_key = "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"  # Replace with your OpenRouter key
openai.api_base = "https://openrouter.ai/api/v1"

import httpx

def ask_deepseek(prompt):
    try:
        headers = {
            "Authorization": "Bearer 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",  # Replace with your real key
            "HTTP-Referer": "http://localhost",      # Required by OpenRouter
            "X-Title": "Personal Assistant"
        }

        body = {
            "model": "amazon/nova-2-lite-v1:free",
            "messages": [
            {
            "role": "system",
            "content": (
            "You are a structured AI assistant. "
            "Do not use markdown symbols such as #, *, or _ for formatting. "
            "Use HTML bold tags <b> and </b> instead of markdown bold. "
            "Whenever you answer, format everything in clean paragraphs. "
            "Each paragraph must contain exactly two sentences. "
            "After two sentences, start a new paragraph by using <br> tags."
            "Do not format headings with #; instead, write headings in plain text followed by a colon. "
            "Always ensure the response is neatly spaced, readable, and broken into multiple two-sentence paragraphs."
            "Always return programming code inside triple-backtick code blocks.Use the language identifier, for example ```java.Preserve all indentation, spacing, and newlines exactly as real code.Never return code in a single line. Always return it formatted."
            )
            },
            {"role": "user", "content": prompt}
            ]
        }

        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=body,
            headers=headers,
            timeout=30.0
        )

        # Ensure status code is OK
        if response.status_code != 200:
            return f"OpenRouter API Error: {response.status_code} - {response.text}"

        data = response.json()

        # Check if 'choices' is present
        if "choices" not in data or len(data["choices"]) == 0:
            return f"Unexpected response format: {data}"

        response_text= data["choices"][0]["message"]["content"].strip()

        code_languages = ["java", "python", "c", "cpp", "javascript", "html", "css"]
        for lang in code_languages:
            response_text = response_text.replace(f"```{lang} ", f"```{lang}\n")

        # Ensure ``` ends on its own line
        response_text = response_text.replace("```", "\n```")

        # Remove accidental extra spaces before or after ```
        response_text = response_text.replace("\n\n```", "\n```").replace("```\n\n", "```\n")

        import re
        response_text = re.sub(r"\*(.*?)\*", r"**\1**", response_text)

        return response_text
    
    except Exception as e:
        return f"Error talking to DeepSeek: {e}"

# -------------------- Voice Input/Output --------------------
engine = pyttsx3.init()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logger.info("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text.lower()
        except sr.UnknownValueError:
            logger.warning("Speech not understood.")
            return None
        except sr.RequestError:
            logger.error("Speech service unreachable.")
            return None
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout.")
            return None

def speak(text):
    engine.say(text)
    engine.runAndWait()

# -------------------- Features --------------------
def set_alarm(alarm_time):
    speak(f"Alarm set for {alarm_time}")
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time == alarm_time:
            speak("Time to wake up!")
            notification.notify(title="Alarm", message="Time to wake up!", timeout=5)
            break
        time.sleep(30)

def open_application(app_name):
    try:
        if not HAS_DISPLAY:
            return "App launching is not available in this environment."
        system = platform.system()
        if system == "Windows":
            os.system(f"start {app_name}")
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        elif system == "Linux":
            subprocess.Popen([app_name])
        speak(f"Opening {app_name}")
        return f"Opening {app_name}"
    except Exception as e:
        logger.error(f"Error opening app: {e}")
        return f"Error opening {app_name}: {e}"

def control_volume(action):
    if not HAS_DISPLAY:
        return "Volume control unavailable in this environment."
    try:
        if platform.system() == "Windows":
            if action == "increase":
                pyautogui.press("volumeup")
            elif action == "decrease":
                pyautogui.press("volumedown")
            elif action == "mute":
                pyautogui.press("volumemute")
        speak(f"Volume {action}d")
        return f"Volume {action}d"
    except Exception as e:
        logger.error(f"Volume error: {e}")
        return f"Error adjusting volume: {e}"

def set_reminder(message, reminder_time):
    speak(f"Reminder set for {reminder_time}")
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time == reminder_time:
            speak(f"Reminder: {message}")
            notification.notify(title="Reminder", message=message, timeout=5)
            break
        time.sleep(30)

def search_web(query):
    try:
        query = query.replace("search", "").strip()
        wikipedia.set_lang("en")
        try:
            suggested = wikipedia.suggest(query)
            if suggested:
                query = suggested
        except:
            pass
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.DisambiguationError as e:
        return f"Be more specific. Options: {', '.join(e.options[:5])}"
    except wikipedia.PageError:
        return f"No result found for '{query}'"
    except Exception as e:
        return f"Search error: {str(e)}"

def translate_text(text, target_lang="fr"):
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|{target_lang}"
        response = requests.get(url).json()
        translated = response['responseData']['translatedText']
        speak(f"Translation: {translated}")
        return translated
    except Exception as e:
        return f"Translation failed: {e}"

# -------------------- Core Command Handler --------------------
def handle_command(command, voice_mode=True, extra_data=None):
    if extra_data is None:
        extra_data = {}

    try:
        command = command.lower()
        logger.info(f"Command received: {command}")

        if "set alarm" in command:
            time_val = extra_data.get('time')
            if time_val:
                set_alarm(time_val)
                response = f"Alarm set for {time_val}"
            else:
                response = "Please provide a time for the alarm."

        elif "open" in command:
            app_name = command.replace("open", "").strip()
            response = open_application(app_name)

        elif "volume" in command:
            if "increase" in command:
                response = control_volume("increase")
            elif "decrease" in command:
                response = control_volume("decrease")
            elif "mute" in command:
                response = control_volume("mute")
            else:
                response = "Specify volume action: increase, decrease, or mute."

        elif "set reminder" in command:
            message = extra_data.get('message')
            time_val = extra_data.get('time')
            if message and time_val:
                set_reminder(message, time_val)
                response = f"Reminder set: {message} at {time_val}"
            else:
                response = "Missing reminder message or time."

        elif "search" in command:
            query = command.replace("search", "").strip()
            response = search_web(query)

        elif "translate" in command:
            text = extra_data.get("text")
            target_lang = extra_data.get("target_lang", "fr")
            if text:
                response = translate_text(text, target_lang)
            else:
                response = "No text provided to translate."

        else:
            response = ask_deepseek(command)

        if voice_mode:
            speak(response)

        return response

    except Exception as e:
        logger.error(f"Error handling command: {str(e)}")
        return "An error occurred while processing your command."
