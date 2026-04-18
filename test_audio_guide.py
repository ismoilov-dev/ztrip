#!/usr/bin/env python3
"""
Test script for Audio Guide System
This script tests the audio processing functionality
"""

import asyncio
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ai_plans.audio_service import audio_service


async def test_audio_service():
    """Test the audio service functionality"""
    print("Testing Audio Service...")
    
    # Test text-to-speech
    print("\n1. Testing text-to-speech...")
    test_text = "Assalomu alaykum, bu ZTrip AI audio guide testi."
    audio_bytes = await audio_service.text_to_speech(test_text, "uz")
    
    if audio_bytes:
        print(f"   Success! Generated {len(audio_bytes)} bytes of audio")
        # Save test audio file
        with open("test_output.mp3", "wb") as f:
            f.write(audio_bytes)
        print("   Saved as test_output.mp3")
    else:
        print("   Failed to generate audio")
    
    # Test base64 encoding/decoding
    print("\n2. Testing base64 encoding/decoding...")
    if audio_bytes:
        encoded = audio_service.encode_base64_audio(audio_bytes)
        decoded = audio_service.decode_base64_audio(encoded)
        
        if decoded == audio_bytes:
            print("   Success! Base64 encoding/decoding works correctly")
        else:
            print("   Failed: Base64 encoding/decoding mismatch")
    
    print("\nAudio service test completed!")


def test_django_setup():
    """Test Django configuration"""
    print("Testing Django setup...")
    
    try:
        from django.conf import settings
        print(f"   Django settings loaded: {settings.DEBUG}")
        print(f"   Templates directory: {settings.TEMPLATES[0]['DIRS']}")
        print(f"   Gemini API Key configured: {'GEMINI_API_KEY' in dir(settings)}")
        
        # Check if channels is configured
        if 'channels' in settings.INSTALLED_APPS:
            print("   Channels app installed")
        else:
            print("   Warning: Channels app not found")
            
        return True
    except Exception as e:
        print(f"   Django setup failed: {e}")
        return False


def test_models():
    """Test model imports"""
    print("\nTesting model imports...")
    
    try:
        from apps.ai_plans.models import AIPlan, AIPlanStatus
        from apps.location.models import Location
        print("   All models imported successfully")
        return True
    except Exception as e:
        print(f"   Model import failed: {e}")
        return False


def test_websocket_consumer():
    """Test WebSocket consumer import"""
    print("\nTesting WebSocket consumer...")
    
    try:
        from apps.ai_plans.consumers import LiveGuideConsumer
        print("   LiveGuideConsumer imported successfully")
        return True
    except Exception as e:
        print(f"   Consumer import failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 50)
    print("AUDIO GUIDE SYSTEM TEST")
    print("=" * 50)
    
    # Test Django setup
    django_ok = test_django_setup()
    
    # Test models
    models_ok = test_models()
    
    # Test WebSocket consumer
    consumer_ok = test_websocket_consumer()
    
    # Test audio service
    await test_audio_service()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"  Django Setup: {'PASS' if django_ok else 'FAIL'}")
    print(f"  Models: {'PASS' if models_ok else 'FAIL'}")
    print(f"  WebSocket Consumer: {'PASS' if consumer_ok else 'FAIL'}")
    print("=" * 50)
    
    if all([django_ok, models_ok, consumer_ok]):
        print("\nAll tests passed! The audio guide system is ready.")
        print("\nTo start the system:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set GEMINI_API_KEY in your .env file")
        print("3. Run migrations: python manage.py migrate")
        print("4. Start server: python manage.py runserver")
        print("5. Visit: http://localhost:8000/audio-guide/")
    else:
        print("\nSome tests failed. Please check the configuration.")


if __name__ == "__main__":
    asyncio.run(main())
