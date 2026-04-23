# WebSocket Testing Guide for AI Audio Guide

This guide covers comprehensive testing approaches for the `LiveGuideConsumer` WebSocket located in `apps/ai_plans/consumers.py`.

## Overview

The `LiveGuideConsumer` handles real-time AI audio guide functionality with the following features:
- JWT authentication
- Location-based context setting
- Text and voice questions
- Multi-language support (Uzbek, Russian, English)
- Travel plan generation
- Audio processing and synthesis

## Testing Approaches

### 1. Unit Testing with Django Channels

**File**: `apps/ai_plans/test_consumers.py`

#### Running Unit Tests
```bash
# Run all WebSocket tests
pytest apps/ai_plans/test_consumers.py

# Run specific test
pytest apps/ai_plans/test_consumers.py::LiveGuideConsumerTests::test_connect_with_valid_token

# Run with verbose output
pytest -v apps/ai_plans/test_consumers.py
```

#### Key Test Cases Covered

1. **Connection Tests**
   - Valid JWT token authentication
   - Invalid token rejection
   - Missing token rejection

2. **Location Management**
   - Setting valid location
   - Invalid location ID handling
   - Location context updates

3. **Question Handling**
   - Text questions with location context
   - Questions without location (error case)
   - AI response processing

4. **Language Support**
   - Valid language switching (uz, ru, en)
   - Invalid language rejection

5. **Voice Processing**
   - Voice question workflow
   - Audio transcription
   - Audio response generation

6. **Plan Generation**
   - Travel plan creation
   - Premium user limits

7. **Error Handling**
   - Invalid JSON messages
   - Missing required fields
   - External service failures

### 2. Manual Testing with Enhanced Script

**File**: `test_websocket_enhanced.py`

#### Setup Requirements

1. **Get JWT Token**
   ```bash
   # Option 1: Command line argument
   python test_websocket_enhanced.py <your_jwt_token>
   
   # Option 2: Environment variable
   export TEST_JWT_TOKEN=<your_jwt_token>
   python test_websocket_enhanced.py
   ```

2. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

#### Running Manual Tests

```bash
# Run all test suites
python test_websocket_enhanced.py <token>

# Or modify the script to run specific tests
python -c "
import asyncio
from test_websocket_enhanced import test_basic_workflow
asyncio.run(test_basic_workflow())
"
```

#### Test Workflow Examples

1. **Basic Connection Test**
   - Connect with JWT token
   - Set location (location_id: 1)
   - Ask text question
   - Receive AI response

2. **Voice Question Test**
   - Connect and set location
   - Send base64-encoded audio
   - Receive transcription and audio response

3. **Language Switching Test**
   - Switch between uz, ru, en
   - Test invalid language rejection

4. **Concurrent Connections Test**
   - Multiple simultaneous connections
   - Verify isolation between clients

### 3. Integration Testing

#### Database Setup for Tests

```python
# Create test data
from apps.location.models import Location
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test user
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)

# Create test locations
Location.objects.create(
    name='Registan Square',
    city='Samarkand',
    type='historical_site',
    description='Historical square in Samarkand'
)
```

#### Mock External Services

```python
# Mock Gemini AI
@patch('apps.ai_plans.consumers.genai.GenerativeModel')
async def test_with_mock_ai(mock_model):
    mock_chat = AsyncMock()
    mock_response = Mock()
    mock_response.text = "Test AI response"
    mock_chat.send_message_async.return_value = mock_response
    mock_model.return_value.start_chat.return_value = mock_chat
    
    # Test logic here...

# Mock Audio Service
@patch('apps.ai_plans.consumers.audio_service')
async def test_with_mock_audio(mock_audio):
    mock_audio.speech_to_text.return_value = "Transcribed text"
    mock_audio.text_to_speech.return_value = b"audio_bytes"
    
    # Test logic here...
```

## Testing Checklist

### ✅ Connection Tests
- [ ] Valid JWT token connects successfully
- [ ] Invalid token rejected with proper error
- [ ] Missing token rejected
- [ ] Connection sends initial welcome message

### ✅ Authentication Tests
- [ ] Expired token rejected
- [ ] Malformed token rejected
- [ ] User not found rejected

### ✅ Location Tests
- [ ] Valid location ID sets context
- [ ] Invalid location ID returns error
- [ ] Location data properly formatted in response
- [ ] Location context included in AI prompts

### ✅ Question Tests
- [ ] Text questions without location return error
- [ ] Text questions with location receive AI response
- [ ] Empty questions ignored
- [ ] AI responses properly formatted

### ✅ Voice Tests
- [ ] Voice questions without location return error
- [ ] Valid audio data processed correctly
- [ ] Transcription sent to client
- [ ] Audio response generated and sent
- [ ] Quota exceeded handled gracefully

### ✅ Language Tests
- [ ] Valid languages (uz, ru, en) accepted
- [ ] Invalid languages rejected
- [ ] Language preference saved for session
- [ ] Audio responses use correct language

### ✅ Plan Generation Tests
- [ ] Valid plan requests processed
- [ ] Missing city parameter returns error
- [ ] Daily limits enforced for non-premium users
- [ ] Premium users bypass limits

### ✅ Error Handling Tests
- [ ] Invalid JSON messages handled gracefully
- [ ] Missing message types handled
- [ ] External service failures don't crash consumer
- [ ] Proper error messages sent to client

## Performance Testing

### Load Testing Script

```python
import asyncio
import websockets
import json

async def load_test(num_clients=10):
    """Test WebSocket performance with multiple clients"""
    tasks = []
    
    for i in range(num_clients):
        task = asyncio.create_task(simulate_client(f"client_{i}"))
        tasks.append(task)
    
    await asyncio.gather(*tasks)

async def simulate_client(client_id):
    """Simulate a single client"""
    uri = f"ws://localhost:8000/ws/live-guide/?token={get_token()}"
    
    async with websockets.connect(uri) as websocket:
        # Simulate typical user interactions
        await websocket.send(json.dumps({
            "type": "set_location",
            "location_id": "1"
        }))
        
        response = await websocket.recv()
        # Handle response...
```

### Memory and Resource Monitoring

```bash
# Monitor WebSocket connections
redis-cli monitor

# Check memory usage
ps aux | grep daphne

# Monitor database connections
python manage.py dbshell
SHOW PROCESSLIST;
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure server is running: `python manage.py runserver`
   - Check WebSocket URL is correct
   - Verify firewall settings

2. **Authentication Failures**
   - Verify JWT token is valid and not expired
   - Check token is properly URL-encoded
   - Ensure user exists in database

3. **Test Timeouts**
   - Increase timeout values in test scripts
   - Check if external services (Gemini API) are accessible
   - Verify mock services are working

4. **Audio Processing Issues**
   - Check audio service dependencies
   - Verify base64 encoding/decoding
   - Test with actual audio files

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In consumer
import logging
logger = logging.getLogger(__name__)

async def receive(self, text_data):
    logger.debug(f"Received message: {text_data}")
    # ... rest of method
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: WebSocket Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.12
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run WebSocket tests
      run: |
        pytest apps/ai_plans/test_consumers.py -v
```

## Best Practices

1. **Mock External Dependencies**: Always mock external APIs and services in unit tests
2. **Test Edge Cases**: Test error conditions and invalid inputs
3. **Clean Test Data**: Use proper setup/teardown to avoid test pollution
4. **Isolate Tests**: Ensure tests don't depend on each other
5. **Performance Monitoring**: Include performance metrics in CI/CD
6. **Security Testing**: Test authentication and authorization thoroughly
7. **Documentation**: Keep test documentation updated with new features

## Running Tests in Different Environments

### Development
```bash
# Local development
pytest apps/ai_plans/test_consumers.py -v -s
```

### Staging
```bash
# Against staging server
STAGING_URL=ws://staging.example.com/ws/live-guide/ python test_websocket_enhanced.py <token>
```

### Production (Read-only)
```bash
# Production monitoring (no data modification)
PRODUCTION_URL=ws://api.example.com/ws/live-guide/ python test_websocket_monitor.py <token>
```
