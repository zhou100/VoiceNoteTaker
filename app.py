from flask import Flask, request, jsonify, g, current_app
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import httpx
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
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client()
)

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
)

# Decorator to monitor API calls
def monitor_api_call(endpoint_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            g.request_id = get_request_id()
            app.logger.info(f"[{g.request_id}] Starting {endpoint_name} request")
            start_time = time.time()
            
            try:
                response = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log the API call completion
                status_code = response[1] if isinstance(response, tuple) else 200
                app.logger.info(
                    f"[{g.request_id}] Completed {endpoint_name} request. "
                    f"Duration: {duration:.2f}s, Status: {status_code}"
                )
                return response
            
            except Exception as e:
                duration = time.time() - start_time
                app.logger.error(
                    f"[{g.request_id}] Error in {endpoint_name} request. "
                    f"Duration: {duration:.2f}s\n{traceback.format_exc()}"
                )
                raise
            
        return decorated_function
    return decorator

@auth.verify_password
def verify_password(username, password):
    if username == os.getenv("API_USERNAME") and password == os.getenv("API_PASSWORD"):
        return username
    return None

@app.route("/")
@auth.login_required
def index():
    return jsonify({
        "message": "Welcome to Voice Note Taker API",
        "endpoints": {
            "/": "API documentation",
            "/api/v1/transcribe": "POST - Upload audio file for transcription",
            "/api/v1/paraphrase": "POST - Paraphrase text"
        }
    })

@app.route("/api/v1/transcribe", methods=["POST"])
@auth.login_required
@limiter.limit("10 per minute")  # Stricter limit for resource-intensive endpoint
@monitor_api_call('transcribe')
def transcribe():
    if not client.api_key or client.api_key == "your_openai_api_key":
        app.logger.error(f"[{g.request_id}] OpenAI API key not configured")
        return jsonify({"error": "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"}), 500

    if "file" not in request.files:
        app.logger.error(f"[{g.request_id}] No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        app.logger.error(f"[{g.request_id}] No selected file")
        return jsonify({"error": "No selected file"}), 400

    try:
        # Generate a unique filename
        temp_path = os.path.join(TEMP_DIR, f"temp_{g.request_id}")
        
        # Save the uploaded file
        file.save(temp_path)
        app.logger.info(f"[{g.request_id}] File saved to {temp_path}")
        
        try:
            # Convert to mp3 (required by Whisper API)
            audio = AudioSegment.from_file(temp_path)
            audio.export(temp_path + ".mp3", format="mp3")
            app.logger.info(f"[{g.request_id}] File converted to MP3")
            
            # Transcribe using OpenAI's Whisper API
            with open(temp_path + ".mp3", "rb") as audio_file:
                app.logger.info(f"[{g.request_id}] Starting transcription with Whisper API")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                
            app.logger.info(f"[{g.request_id}] Successfully transcribed audio")
            return transcript.text + "\n\n" + "Paraphrased version will be available after calling the paraphrase endpoint."
            
        finally:
            # Clean up temporary files
            try:
                os.remove(temp_path)
                os.remove(temp_path + ".mp3")
                app.logger.info(f"[{g.request_id}] Cleaned up temporary files")
            except Exception as e:
                app.logger.warning(f"[{g.request_id}] Error cleaning up files: {str(e)}")
    
    except Exception as e:
        app.logger.error(f"[{g.request_id}] Error processing audio: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Error processing audio file"}), 500

@app.route("/api/v1/paraphrase", methods=["POST"])
@auth.login_required
@limiter.limit("30 per minute")  # Less strict limit for text-based endpoint
@monitor_api_call('paraphrase')
def get_paraphrase():
    if not client.api_key or client.api_key == "your_openai_api_key":
        app.logger.error(f"[{g.request_id}] OpenAI API key not configured")
        return jsonify({"error": "OpenAI API key not configured"}), 500

    if not request.is_json:
        app.logger.error(f"[{g.request_id}] Request must be JSON")
        return jsonify({"error": "Request must be JSON"}), 400
    
    text = request.json.get("text")
    if not text:
        app.logger.error(f"[{g.request_id}] No text provided")
        return jsonify({"error": "No text provided"}), 400
    
    try:
        app.logger.info(f"[{g.request_id}] Processing paraphrase request")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant that paraphrases text to make it more clear and concise while preserving the original meaning."},
                {"role": "user", "content": f"Please paraphrase this text: {text}"}
            ]
        )
        
        app.logger.info(f"[{g.request_id}] Successfully received paraphrase response")
        paraphrased = response.choices[0].message.content.strip()
        
        return text + "\n\n" + paraphrased
    except Exception as e:
        app.logger.error(f"[{g.request_id}] Error paraphrasing text: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Error paraphrasing text"}), 500

# Error handler for rate limit exceeded
@app.errorhandler(429)
def ratelimit_handler(e):
    app.logger.warning(f"Rate limit exceeded: {e.description}")
    return jsonify({"error": f"Rate limit exceeded: {e.description}"}), 429

# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found_error(e):
    app.logger.info(f"404 error: {request.url}")
    return jsonify({
        "error": "The requested URL was not found",
        "available_endpoints": {
            "/": "API documentation",
            "/api/v1/transcribe": "POST - Upload audio file for transcription",
            "/api/v1/paraphrase": "POST - Paraphrase text"
        }
    }), 404

# Error handler for all other exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Print debug information
    app.logger.info(f"System PATH: {os.environ['PATH']}")
    
    # In development only
    app.run(debug=True, host="0.0.0.0", port=5000)
