# AI Audio Guide System

A complete audio guide system using Django, WebSocket, and Gemini API that allows users to send voice messages and receive audio responses.

## Features

- **Voice Input**: Users can record audio messages using their device microphone
- **Speech-to-Text**: Converts voice input to text using Google Speech Recognition
- **AI Responses**: Processes questions using Google Gemini API with location context
- **Text-to-Speech**: Converts AI responses back to audio using Edge TTS
- **Multi-language Support**: Uzbek, Russian, and English languages
- **Real-time Communication**: WebSocket-based real-time interaction
- **Location Context**: AI responses are contextualized based on selected tourist locations

## Architecture

```
Frontend (HTML/JS) <-> WebSocket Consumer <-> Audio Service <-> Gemini API
                                      |
                                      v
                               Django Models
```

### Components

1. **Audio Service** (`apps/ai_plans/audio_service.py`)
   - Speech-to-text conversion
   - Text-to-speech generation
   - Audio encoding/decoding

2. **WebSocket Consumer** (`apps/ai_plans/consumers.py`)
   - Handles real-time communication
   - Manages audio message processing
   - Integrates with Gemini API

3. **Frontend Interface** (`templates/audio_guide.html`)
   - Audio recording interface
   - Language selection
   - Location selection
   - Audio playback

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Add to your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Database Setup

```bash
python manage.py migrate
```

### 4. Run Tests

```bash
python test_audio_guide.py
```

### 5. Start Development Server

```bash
python manage.py runserver
```

## Usage

### Access the Audio Guide

Visit: `http://localhost:8000/audio-guide/`

### Authentication

The system requires JWT authentication. You'll need to provide a valid auth token.

### Workflow

1. **Select Location**: Choose a tourist location from the dropdown
2. **Select Language**: Choose between Uzbek, Russian, or English
3. **Record Voice**: Click the red record button and speak your question
4. **Get Response**: The system will:
   - Transcribe your voice to text
   - Send the question to Gemini AI
   - Generate an audio response
   - Play the response automatically

## API Endpoints

### WebSocket Connection

```
ws://localhost:8000/ws/live-guide/?token=your_jwt_token
```

### Message Types

#### Client to Server

- `set_location`: Set current location context
- `voice_question`: Send voice message
- `set_language`: Change audio language
- `question`: Send text question (existing functionality)

#### Server to Client

- `connected`: Connection established
- `location_set`: Location context updated
- `processing_voice`: Voice input being processed
- `transcribed`: Voice converted to text
- `thinking`: AI processing request
- `generating_audio`: Audio response being generated
- `audio_answer`: Complete audio response
- `answer`: Text response (fallback)
- `error`: Error messages

## Audio Processing

### Supported Formats

- **Input**: WebM, WAV, MP3 (browser recording)
- **Output**: MP3 (Edge TTS)

### Languages

- **Uzbek** (`uz`): uz-UZ-MadinaNeural voice
- **Russian** (`ru`): ru-RU-SvetlanaNeural voice  
- **English** (`en`): en-US-JennyNeural voice

### Fallback Options

- **Speech Recognition**: Google Speech Recognition -> Sphinx (offline)
- **Text-to-Speech**: Edge TTS -> gTTS

## Configuration

### Django Settings

Ensure these are configured in `config/settings.py`:

```python
# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        # ...
    }
]

# Channels (for WebSocket)
ASGI_APPLICATION = "config.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}
```

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## File Structure

```
apps/ai_plans/
    audio_service.py      # Audio processing service
    consumers.py          # WebSocket consumer (enhanced)
    views.py              # Django views (audio_guide_view added)
    urls.py               # URL routing (audio-guide/ added)

templates/
    audio_guide.html      # Frontend interface

test_audio_guide.py       # System test script
```

## Troubleshooting

### Common Issues

1. **Microphone Permission**: Ensure browser has microphone access
2. **WebSocket Connection**: Check JWT token validity
3. **Audio Quality**: Use quiet environment for better speech recognition
4. **Gemini API**: Verify API key is valid and has quota

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Run the test script to verify system components:

```bash
python test_audio_guide.py
```

## Development

### Adding New Languages

1. Update `audio_service.py` language mappings
2. Add voice options to Edge TTS
3. Update frontend language buttons
4. Update Gemini system instructions

### Customizing AI Responses

Edit the system instruction in `consumers.py`:

```python
system_instruction=(
    "Sen ZTrip AI audio guidsan. "
    "Foydalanuvchi turistik joy haqida savol beradi. "
    "Qisqa, aniq va qiziqarli javob ber (2-3 jumla). "
    "O'zbek, Rus yoki Ingliz tilida javob ber."
)
```

## Performance Considerations

- Audio files are processed in memory (no persistent storage)
- Temporary files are cleaned up automatically
- WebSocket connections are stateful per user
- Gemini API calls are asynchronous

## Security

- JWT authentication required
- Audio data is base64 encoded
- Temporary files are securely handled
- No persistent audio storage

## License

This audio guide system is part of the ZTrip travel application project.
