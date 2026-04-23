import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken
from config.asgi import application
from apps.location.models import Location
from .consumers import LiveGuideConsumer
from .models import AIPlan, AIPlanStatus

User = get_user_model()


class LiveGuideConsumerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = AccessToken.for_user(self.user)
        self.location = Location.objects.create(
            name='Test Location',
            city='Test City',
            type='museum',
            description='Test description'
        )

    async def test_connect_with_valid_token(self):
        """Test successful WebSocket connection with valid JWT token"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Check initial connection message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connected')
        self.assertIn('AI Guide tayyor', response['message'])
        
        await communicator.disconnect()

    async def test_connect_without_token(self):
        """Test connection rejection without token"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            "/ws/live-guide/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_connect_with_invalid_token(self):
        """Test connection rejection with invalid token"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            "/ws/live-guide/?token=invalid_token"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    @patch('apps.ai_plans.consumers.settings')
    async def test_set_location_success(self, mock_settings):
        """Test successful location setting"""
        mock_settings.GEMINI_API_KEY = 'test_key'
        
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Send location setting message
        await communicator.send_json_to({
            'type': 'set_location',
            'location_id': self.location.id
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'location_set')
        self.assertEqual(response['location']['id'], self.location.id)
        
        await communicator.disconnect()

    async def test_set_location_invalid_id(self):
        """Test location setting with invalid ID"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Send invalid location ID
        await communicator.send_json_to({
            'type': 'set_location',
            'location_id': 99999
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('Location topilmadi', response['message'])
        
        await communicator.disconnect()

    @patch('apps.ai_plans.consumers.settings')
    @patch('apps.ai_plans.consumers.genai.GenerativeModel')
    async def test_question_success(self, mock_model, mock_settings):
        """Test successful question handling"""
        mock_settings.GEMINI_API_KEY = 'test_key'
        
        # Mock Gemini response
        mock_chat = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Test answer"
        mock_chat.send_message_async.return_value = mock_response
        mock_model.return_value.start_chat.return_value = mock_chat
        
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Set location first
        await communicator.send_json_to({
            'type': 'set_location',
            'location_id': self.location.id
        })
        await communicator.receive_json_from()
        
        # Send question
        await communicator.send_json_to({
            'type': 'question',
            'text': 'What is this place?'
        })
        
        # Should receive thinking message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'thinking')
        
        # Should receive answer
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'answer')
        self.assertEqual(response['text'], 'Test answer')
        
        await communicator.disconnect()

    async def test_question_without_location(self):
        """Test question without setting location first"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Send question without setting location
        await communicator.send_json_to({
            'type': 'question',
            'text': 'What is this place?'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('Avval set_location yuboring', response['message'])
        
        await communicator.disconnect()

    async def test_language_setting(self):
        """Test language setting functionality"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Test valid language
        await communicator.send_json_to({
            'type': 'set_language',
            'language': 'en'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'language_set')
        self.assertEqual(response['language'], 'en')
        
        # Test invalid language
        await communicator.send_json_to({
            'type': 'set_language',
            'language': 'invalid'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn("Qo'llab-quvvatlanmaydigan til", response['message'])
        
        await communicator.disconnect()

    @patch('apps.ai_plans.consumers.settings')
    @patch('apps.ai_plans.consumers.audio_service')
    async def test_voice_question(self, mock_audio_service, mock_settings):
        """Test voice question processing"""
        mock_settings.GEMINI_API_KEY = 'test_key'
        
        # Mock audio service
        mock_audio_service.decode_base64_audio.return_value = b'fake_audio'
        mock_audio_service.speech_to_text.return_value = 'What is this place?'
        mock_audio_service.text_to_speech.return_value = b'audio_response'
        mock_audio_service.encode_base64_audio.return_value = 'base64_audio'
        
        # Mock Gemini response
        mock_chat = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Test answer"
        mock_chat.send_message_async.return_value = mock_response
        
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Set location first
        await communicator.send_json_to({
            'type': 'set_location',
            'location_id': self.location.id
        })
        await communicator.receive_json_from()
        
        # Send voice question
        await communicator.send_json_to({
            'type': 'voice_question',
            'audio': 'fake_base64_audio',
            'language': 'uz'
        })
        
        # Should receive processing_voice
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'processing_voice')
        
        # Should receive transcribed
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'transcribed')
        self.assertEqual(response['text'], 'What is this place?')
        
        # Should receive thinking
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'thinking')
        
        # Should receive generating_audio
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'generating_audio')
        
        # Should receive audio_answer
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'audio_answer')
        self.assertEqual(response['text'], 'Test answer')
        self.assertEqual(response['audio'], 'base64_audio')
        
        await communicator.disconnect()

    @patch('apps.ai_plans.consumers.settings')
    async def test_generate_plan(self, mock_settings):
        """Test travel plan generation"""
        mock_settings.GEMINI_API_KEY = 'test_key'
        
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial connection message
        await communicator.receive_json_from()
        
        # Send plan generation request
        await communicator.send_json_to({
            'type': 'generate_plan',
            'city': 'Tashkent',
            'days': 3,
            'budget': 1000,
            'language': 'uz'
        })
        
        # Should receive generating message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'generating')
        
        await communicator.disconnect()

    async def test_invalid_json_message(self):
        """Test handling of invalid JSON messages"""
        communicator = WebsocketCommunicator(
            LiveGuideConsumer.as_asgi(),
            f"/ws/live-guide/?token={self.token}"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Send invalid JSON
        await communicator.send_to('invalid json')
        
        # Should not crash or send response
        await communicator.disconnect()

# Integration Tests
class LiveGuideConsumerIntegrationTests(TestCase):
    """Integration tests for WebSocket consumer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = AccessToken.for_user(self.user)

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: connect -> set location -> ask question -> disconnect"""
        # This would require setting up test database with locations
        # and mocking external services
        pass
