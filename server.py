from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from base_model import (
    listen, speak, ask_deepseek, set_alarm,
    open_application, control_volume, set_reminder,
    search_web, translate_text, handle_command
)
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/reminders')
def reminders():
    return render_template('reminders.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# Unified command API
@app.route('/api/process_command', methods=['POST'])
def process_command():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        command = data.get('command', '')
        command_type = data.get('type', 'text')  # "text" or "voice"
        if not command:
            return jsonify({"error": "No command provided"}), 400

        extra_data = {k: v for k, v in data.items() if k not in ['command', 'type']}
        voice_mode = command_type == "voice"
        response = handle_command(command, voice_mode, extra_data)

        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# Voice recognition endpoint
@app.route('/api/voice/start', methods=['POST'])
def start_voice():
    try:
        text = listen()
        if text:
            return jsonify({"text": text})
        return jsonify({"error": "Could not understand audio"}), 400
    except Exception as e:
        logger.error(f"Error in voice recognition: {str(e)}")
        return jsonify({"error": "Error processing voice input"}), 500

# Run server
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='192.168.1.13', port=5000, debug=False)
