# Voice Note Taker API

A Flask-based API for transcribing audio files and paraphrasing text.

## Features

- Audio file transcription using OpenAI's Whisper API
- Text paraphrasing using GPT-4o-mini
- Rate limiting and authentication
- Docker support
- Production-ready with gunicorn

## API Usage

### Authentication

The API uses HTTP Basic Authentication. You'll need to:
1. Get your API credentials from your administrator
2. Base64 encode them in the format `username:password`
3. Add the encoded string to your Authorization header

Example:
```bash
# Replace with your actual credentials
echo -n "your_username:your_password" | base64
# Add the result to your Authorization header:
# Authorization: Basic <base64_string>
```

### Endpoints

#### 1. Transcribe Audio
Transcribes an audio file to text.

**Request:**
```bash
curl -X POST "https://your-render-url/api/v1/transcribe" \
  -H "Authorization: Basic <your_base64_credentials>" \
  -F "file=@path_to_your_audio.wav"
```

**Response:**
```json
{
    "text": "transcribed text here"
}
```

#### 2. Paraphrase Text
Paraphrases the given text.

**Request:**
```bash
curl -X POST "https://your-render-url/api/v1/paraphrase" \
  -H "Authorization: Basic <your_base64_credentials>" \
  -H "Content-Type: application/json" \
  -d '{"text": "text to paraphrase"}'
```

**Response:**
```json
{
    "original": "text to paraphrase",
    "paraphrased": "paraphrased version of the text"
}
```

## Rate Limits

- Transcription: 10 requests per minute
- Paraphrasing: 30 requests per minute
- Global: 200 requests per day, 50 per hour

## Error Handling

The API returns appropriate HTTP status codes and error messages:

```json
{
    "error": "Error message here"
}
```

Common status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 429: Too Many Requests
- 500: Internal Server Error

## Local Development

1. Clone the repository
2. Create a `.env` file with:
   ```
   API_USERNAME=your_username
   API_PASSWORD=your_password
   OPENAI_API_KEY=your_openai_api_key
   FLASK_ENV=development
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   python app.py
   ```

## Deployment to Render

1. **Fork/Clone Repository**
   - Fork this repository to your GitHub account
   - Or clone it and push to your own repository

2. **Create Render Account**
   - Sign up at [dashboard.render.com](https://dashboard.render.com)
   - Connect your GitHub account

3. **Create New Web Service**
   - Click "New +"
   - Select "Web Service"
   - Choose your repository
   - Select "Docker" as the environment

4. **Configure Service**
   - Name: `voice-note-taker` (or your preferred name)
   - Region: Choose closest to your users
   - Branch: main (or your default branch)
   - Plan: Free

5. **Set Environment Variables**
   Add the following environment variables in Render dashboard:
   - `API_USERNAME`: Your chosen API username
   - `API_PASSWORD`: Your chosen API password
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_ENV`: production

6. **Deploy**
   - Click "Create Web Service"
   - Wait for the build and deployment to complete
   - Your API will be available at the URL provided by Render