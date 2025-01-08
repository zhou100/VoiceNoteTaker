# Scratchpad

## Current Task
Deploy voice transcription and paraphrasing service

### Requirements
- Endpoints:
  - POST /api/v1/transcribe (for audio file upload)
  - GET /api/v1/paraphrase (for viewing results)
- Authentication system to restrict access
- iOS Shortcuts integration instructions

### Plan
[X] Set up Flask application with required endpoints
[X] Add authentication middleware
[X] Configure Gunicorn/uWSGI
[X] Set up Nginx as reverse proxy
[X] Add error handling and logging
[X] Create deployment workflow
[X] Update deployment documentation
[X] Add iOS Shortcuts integration guide

### Deployment Options (Cheapest to Most Expensive)
1. Render (Free tier available)
   - Web Services start at $7/month
   - Good for small apps
   - Easy deployment

2. Fly.io (Good free tier)
   - Free tier with 3 shared-cpu VMs
   - Starts at $1.94/month for paid
   - Good documentation

3. PythonAnywhere ($5/month)
   - Python-specific hosting
   - Easy to use
   - Good for beginners

### Deployment Instructions
1. Choose hosting platform
2. Prepare for deployment:
   - Set up environment variables
   - Configure logging for production
   - Add proper CORS headers
   - Set up monitoring

### iOS Integration Notes
- Use Base64 encoded credentials in Authorization header
- Format: `Basic <base64(username:password)>`
- Headers must be added to each "Get Contents of URL" action
- Form data required for audio file upload

## Progress

[X] Converted web app to API-only service
[X] Implemented HTTP Basic Authentication
[X] Added root endpoint with API documentation
[X] Tested transcribe and paraphrase endpoints
[X] Updated README.md with comprehensive API documentation
[X] Added iOS Shortcuts integration instructions

## Lessons Learned

1. When using Flask's `render_template`, make sure to put HTML files in the `templates` directory
2. When serving an API, it's better to use `jsonify` for consistent JSON responses
3. Base64 encoded credentials for HTTP Basic Auth: `dm9pY2Vub3RlX2FwaTpWTlRfc2VjdXJlXzIwMjUh`
4. Important to handle CORS if the API will be accessed from web browsers
5. Keep API credentials in environment variables for security

## Task Progress

## Current Task: Fix API Errors
Found two issues in the logs:
1. 404 Not Found error - This indicates a routing issue where the requested URL was not found
2. OpenAI API error in paraphrase endpoint - Using incorrect model name "gpt-4o-mini"

### Plan
[X] Fix the model name in paraphrase endpoint (changed to "gpt-4")
[X] Add proper error handling for invalid routes (added 404 handler with helpful endpoint info)
[ ] Test the fixes
[ ] Update documentation with correct model information

## Lessons
1. When using Flask's current_app, make sure to import it from flask: `from flask import current_app`
2. Handle both tuple responses (response, status_code) and direct response objects in decorators
3. Use request IDs consistently in log messages for better traceability
4. Log API call completion with duration and status code for monitoring
5. Use appropriate log levels (INFO for success, ERROR for failures)
6. Add helpful error messages for 404s that guide users to valid endpoints
7. Don't make assumptions about API configurations - verify with documentation or team first

## Next Steps
[ ] Add more detailed logging for the paraphrase endpoint
[ ] Consider adding request/response payload logging (with sensitive data redaction)
[ ] Add structured logging for better log analysis
[ ] Set up log rotation to manage log file sizes

## Current Task: Testing Voice API Functionality
[X] Set up ffmpeg for audio processing
[X] Configure OpenAI API key
[X] Update to latest OpenAI client library
[X] Successfully test audio transcription endpoint
[X] Add rate limiting to protect API endpoints

## Lessons
1. ffmpeg binaries need to be properly configured:
   - Place ffmpeg binaries in a `ffmpeg` directory
   - Add ffmpeg directory to system PATH
   - Set explicit paths for FFMPEG_PATH and FFPROBE_PATH in pydub

2. OpenAI API Integration:
   - Use the latest OpenAI client library: `from openai import OpenAI`
   - Initialize client with: `client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))`
   - Use the new client.audio.transcriptions.create() method for Whisper API
   - Access transcription text with `transcript.text` instead of `transcript["text"]`

3. Rate Limiting:
   - Use Flask-Limiter for rate limiting
   - Set different limits for different endpoints based on resource intensity
   - Identify users by authenticated username or IP address
   - Use in-memory storage for development, consider Redis for production
   - Add custom error handler for rate limit exceeded responses

## Next Steps
1. [ ] Implement the paraphrase endpoint using OpenAI's GPT API
2. [ ] Add proper logging and monitoring
3. [ ] Consider adding API key rotation mechanism
4. [ ] Plan for production deployment
   - [ ] Set up Redis for rate limiting storage
   - [ ] Configure proper logging
   - [ ] Set up monitoring
   - [ ] Configure CORS if needed

## Current Task: Implementing End-to-End Voice Processing

## Progress
[X] Implement paraphrase endpoint using gpt-3.5-turbo
[X] Test end-to-end flow:
  - Audio upload → Transcription → Paraphrasing
[X] Add proper error handling and logging for both endpoints

## Lessons
1. When using Flask's current_app, make sure to import it from flask: `from flask import current_app`
2. Handle both tuple responses (response, status_code) and direct response objects in decorators
3. Use request IDs consistently in log messages for better traceability
4. Log API call completion with duration and status code for monitoring
5. Use appropriate log levels (INFO for success, ERROR for failures)
6. Always check OpenAI API key configuration before making API calls
7. Use gpt-3.5-turbo for faster and more cost-effective processing
8. Keep system prompts clear and focused for better results

## Next Steps
[ ] Add support for longer audio files
[ ] Implement batch processing for multiple files
[ ] Add support for different output formats
[ ] Consider adding caching for frequently requested paraphrases
[ ] Set up proper rate limiting with Redis for production

## Current Task: Deployment Planning

## Progress
[X] Implement paraphrase endpoint using gpt-3.5-turbo
[X] Test end-to-end flow:
  - Audio upload → Transcription → Paraphrasing
[X] Add proper error handling and logging for both endpoints

## Next Steps
[ ] Choose hosting platform
[ ] Prepare for deployment:
    - [ ] Set up environment variables
    - [ ] Configure logging for production
    - [ ] Add proper CORS headers
    - [ ] Set up monitoring
[ ] Add support for longer audio files
[ ] Set up proper rate limiting with Redis
[ ] Add caching for frequently requested paraphrases

## Lessons
1. When using Flask's current_app, make sure to import it from flask: `from flask import current_app`
2. Handle both tuple responses (response, status_code) and direct response objects in decorators
3. Use request IDs consistently in log messages for better traceability
4. Log API call completion with duration and status code for monitoring
5. Use appropriate log levels (INFO for success, ERROR for failures)
6. Always check OpenAI API key configuration before making API calls
7. Use gpt-3.5-turbo for faster and more cost-effective processing
8. Keep system prompts clear and focused for better results
