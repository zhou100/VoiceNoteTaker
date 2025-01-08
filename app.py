from flask import Flask, request, jsonify, g, current_app
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import traceback
import sys
import time
from functools import wraps
from logging_config import setup_logging, log_api_call, get_request_id

# Load environment variables
load_dotenv()

# Configure paths
current_dir = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(current_dir, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

app = Flask(__name__)
auth = HTTPBasicAuth()

# Set up logging
setup_logging(app)

# Configure OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key or client.api_key == "your_openai_api_key":
    app.logger.error("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")

# Configure rate limiter
def get_auth_username():
    auth_username = auth.get_auth()
    return auth_username if auth_username else get_remote_address()

limiter = Limiter(
    key_func=get_auth_username,  # Rate limit by authenticated username or IP
    app=app,
    default_limits=["200 per day", "50 per hour"],  # Global limits
    storage_uri="memory://"  # Use in-memory storage (change to redis:// for production)
)

# In production, use a proper user database
users = {
    os.getenv("API_USERNAME", "admin"): generate_password_hash(os.getenv("API_PASSWORD", "change_me_in_production"))
}

def monitor_api_call(endpoint_name):
    """Decorator to monitor API calls"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate request ID and store it in g and request
            request_id = get_request_id()
            g.request_id = request_id
            request.request_id = request_id
            
            app.logger.info(f"[{request_id}] Starting {endpoint_name} request")
            
            start_time = time.time()
            try:
                response = f(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Handle tuple response (response, status_code)
                if isinstance(response, tuple):
                    status_code = response[1]
                    response_obj = response[0]
                else:
                    status_code = 200
                    response_obj = response
                
                log_api_call(endpoint_name, duration_ms, (response_obj, status_code))
                return response
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_response = jsonify({"error": str(e)})
                log_api_call(endpoint_name, duration_ms, (error_response, 500))
                app.logger.error(f"[{request_id}] Error in {endpoint_name}: {str(e)}\n{traceback.format_exc()}")
                return error_response, 500
        return decorated_function
    return decorator

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

@app.route('/')
@limiter.exempt  # No rate limit for index page
@monitor_api_call('index')
def index():
    return jsonify({"message": "Welcome to Voice Note Taker API", 
                   "endpoints": {
                       "/api/v1/transcribe": "POST - Upload audio file for transcription",
                       "/api/v1/paraphrase": "POST - Paraphrase text"
                   }}), 200

@app.route('/api/v1/transcribe', methods=['POST'])
@auth.login_required
@limiter.limit("10 per minute")  # Stricter limit for resource-intensive endpoint
@monitor_api_call('transcribe')
def transcribe():
    if not client.api_key or client.api_key == "your_openai_api_key":
        app.logger.error(f"[{g.request_id}] OpenAI API key not configured")
        return jsonify({"error": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"}), 500

    if 'file' not in request.files:
        app.logger.warning(f"[{g.request_id}] No file provided in request")
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        app.logger.warning(f"[{g.request_id}] Empty filename provided")
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save the uploaded file temporarily
        temp_path = os.path.join(TEMP_DIR, "temp_audio")
        file.save(temp_path)
        app.logger.info(f"[{g.request_id}] Saved temporary file: {temp_path}")
        
        try:
            # Convert audio to format compatible with OpenAI's Whisper
            audio = AudioSegment.from_file(temp_path)
            audio.export(temp_path + ".mp3", format="mp3")
            app.logger.info(f"[{g.request_id}] Successfully converted audio to MP3")
        except Exception as e:
            app.logger.error(f"[{g.request_id}] Error converting audio: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"error": "Error converting audio file. Make sure it's a valid audio format"}), 500
        
        try:
            # Transcribe using OpenAI's Whisper API
            with open(temp_path + ".mp3", "rb") as audio_file:
                app.logger.info(f"[{g.request_id}] Starting transcription with Whisper API")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                app.logger.info(f"[{g.request_id}] Successfully transcribed audio")
        except Exception as e:
            app.logger.error(f"[{g.request_id}] Error transcribing with Whisper API: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"error": "Error transcribing audio with Whisper API"}), 500
        
        # Clean up temporary files
        os.remove(temp_path)
        os.remove(temp_path + ".mp3")
        app.logger.info(f"[{g.request_id}] Cleaned up temporary files")
        
        return jsonify({"text": transcript.text}), 200
    
    except Exception as e:
        app.logger.error(f"[{g.request_id}] Error processing audio: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"Error processing audio file: {str(e)}"}), 500
    finally:
        # Ensure temp files are cleaned up even if an error occurs
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_path + ".mp3"):
            os.remove(temp_path + ".mp3")

@app.route('/api/v1/paraphrase', methods=['POST'])
@auth.login_required
@limiter.limit("30 per minute")  # Less strict limit for text-based endpoint
@monitor_api_call('paraphrase')
def get_paraphrase():
    if not client.api_key or client.api_key == "your_openai_api_key":
        app.logger.error(f"[{g.request_id}] OpenAI API key not configured")
        return jsonify({"error": "OpenAI API key not configured"}), 500

    if not request.is_json:
        app.logger.warning(f"[{g.request_id}] Invalid content type")
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        app.logger.warning(f"[{g.request_id}] No text provided in request")
        return jsonify({"error": "No text provided in request body"}), 400
    
    try:
        app.logger.info(f"[{g.request_id}] Processing paraphrase request")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-3.5-turbo for faster and cheaper processing
            messages=[
                {"role": "system", "content": "You are a helpful assistant that paraphrases text to make it more clear and concise while preserving the original meaning."},
                {"role": "user", "content": f"Please paraphrase the following text:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        paraphrased_text = response.choices[0].message.content.strip()
        app.logger.info(f"[{g.request_id}] Successfully paraphrased text")
        
        return jsonify({
            "original": text,
            "paraphrased": paraphrased_text
        }), 200
    except Exception as e:
        app.logger.error(f"[{g.request_id}] Error paraphrasing text: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"Error processing text: {str(e)}"}), 500

# Error handler for rate limit exceeded
@app.errorhandler(429)
def ratelimit_handler(e):
    app.logger.warning(f"Rate limit exceeded: {e.description}")
    return jsonify({"error": f"Rate limit exceeded: {e.description}"}), 429

# Error handler for all other exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # Print debug information
    app.logger.info(f"System PATH: {os.environ['PATH']}")
    
    # In development only
    app.run(debug=True, host='127.0.0.1', port=5000)
