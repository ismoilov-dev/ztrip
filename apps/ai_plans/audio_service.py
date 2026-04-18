import os
import tempfile
import base64
import asyncio
import io
from typing import Optional
import speech_recognition as sr
from gtts import gTTS
import edge_tts
from pydub import AudioSegment
import cv2
import numpy as np
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AudioService:
    """Service for handling speech-to-text and text-to-speech operations"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.temp_dir = tempfile.gettempdir()
        
    async def speech_to_text(self, audio_data: bytes, language: str = "uz") -> Optional[str]:
        """
        Convert audio data to text using speech recognition
        
        Args:
            audio_data: Raw audio data bytes
            language: Language code (uz, ru, en)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Save audio data to temporary file
            temp_audio_path = os.path.join(self.temp_dir, f"temp_audio_{id(audio_data)}.wav")
            
            # Convert bytes to audio file
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            audio.export(temp_audio_path, format="wav")
            
            # Use speech recognition
            with sr.AudioFile(temp_audio_path) as source:
                audio_data_rec = self.recognizer.record(source)
                
            # Map language codes for speech recognition
            lang_map = {
                "uz": "uz-UZ",  # Uzbek
                "ru": "ru-RU",  # Russian  
                "en": "en-US"   # English
            }
            
            sr_language = lang_map.get(language, "uz-UZ")
            
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio_data_rec, language=sr_language)
                return text
            except sr.UnknownValueError:
                # Fallback to Sphinx (offline)
                text = self.recognizer.recognize_sphinx(audio_data_rec)
                return text
                
        except Exception as e:
            logger.error(f"Speech to text error: {str(e)}")
            return None
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
    
    async def text_to_speech(self, text: str, language: str = "uz") -> Optional[bytes]:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            language: Language code (uz, ru, en)
            
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            # Map language codes for TTS
            voice_map = {
                "uz": "uz-UZ-MadinaNeural",  # Uzbek female voice
                "ru": "ru-RU-SvetlanaNeural", # Russian female voice
                "en": "en-US-JennyNeural"     # English female voice
            }
            
            voice = voice_map.get(language, "uz-UZ-MadinaNeural")
            
            # Use edge-tts for better quality
            communicate = edge_tts.Communicate(text, voice)
            
            # Generate audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return audio_data if audio_data else None
            
        except Exception as e:
            logger.error(f"Text to speech error: {str(e)}")
            # Fallback to gTTS
            try:
                gtts_lang_map = {
                    "uz": "uz",  # Uzbek
                    "ru": "ru",  # Russian
                    "en": "en"   # English
                }
                
                gtts_lang = gtts_lang_map.get(language, "uz")
                tts = gTTS(text=text, lang=gtts_lang, slow=False)
                
                # Save to temporary file and read as bytes
                temp_mp3_path = os.path.join(self.temp_dir, f"temp_tts_{id(text)}.mp3")
                tts.save(temp_mp3_path)
                
                with open(temp_mp3_path, "rb") as f:
                    audio_data = f.read()
                
                # Clean up
                os.remove(temp_mp3_path)
                return audio_data
                
            except Exception as fallback_error:
                logger.error(f"TTS fallback error: {str(fallback_error)}")
                return None
    
    def decode_base64_audio(self, base64_data: str) -> Optional[bytes]:
        """
        Decode base64 audio data to bytes
        
        Args:
            base64_data: Base64 encoded audio string
            
        Returns:
            Audio bytes or None if failed
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            audio_bytes = base64.b64decode(base64_data)
            return audio_bytes
        except Exception as e:
            logger.error(f"Base64 decode error: {str(e)}")
            return None
    
    def encode_base64_audio(self, audio_bytes: bytes) -> str:
        """
        Encode audio bytes to base64 string
        
        Args:
            audio_bytes: Audio data bytes
            
        Returns:
            Base64 encoded string
        """
        try:
            base64_data = base64.b64encode(audio_bytes).decode('utf-8')
            return base64_data
        except Exception as e:
            logger.error(f"Base64 encode error: {str(e)}")
            return ""
    
    async def extract_audio_from_video(self, video_data: bytes) -> Optional[bytes]:
        """
        Extract audio from video file
        
        Args:
            video_data: Video file bytes
            
        Returns:
            Audio bytes or None if failed
        """
        try:
            # Save video to temporary file
            temp_video_path = os.path.join(self.temp_dir, f"temp_video_{id(video_data)}.mp4")
            temp_audio_path = os.path.join(self.temp_dir, f"temp_audio_{id(video_data)}.wav")
            
            with open(temp_video_path, "wb") as f:
                f.write(video_data)
            
            # Extract audio using moviepy or ffmpeg
            try:
                from moviepy.editor import VideoFileClip
                video = VideoFileClip(temp_video_path)
                audio = video.audio
                audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
                video.close()
            except ImportError:
                # Fallback to ffmpeg if moviepy not available
                import subprocess
                subprocess.run([
                    'ffmpeg', '-i', temp_video_path, 
                    '-vn', '-acodec', 'pcm_s16le', 
                    '-ar', '16000', '-ac', '1', 
                    temp_audio_path
                ], capture_output=True, check=True)
            
            # Read audio file
            with open(temp_audio_path, "rb") as f:
                audio_bytes = f.read()
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Video audio extraction error: {str(e)}")
            return None
        finally:
            # Clean up temporary files
            for path in [temp_video_path, temp_audio_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    def decode_base64_video(self, base64_data: str) -> Optional[bytes]:
        """
        Decode base64 video data to bytes
        
        Args:
            base64_data: Base64 encoded video string
            
        Returns:
            Video bytes or None if failed
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            video_bytes = base64.b64decode(base64_data)
            return video_bytes
        except Exception as e:
            logger.error(f"Video base64 decode error: {str(e)}")
            return None
    
    def encode_base64_video(self, video_bytes: bytes) -> str:
        """
        Encode video bytes to base64 string
        
        Args:
            video_bytes: Video data bytes
            
        Returns:
            Base64 encoded string
        """
        try:
            base64_data = base64.b64encode(video_bytes).decode('utf-8')
            return base64_data
        except Exception as e:
            logger.error(f"Video base64 encode error: {str(e)}")
            return ""
    
    async def process_video_input(self, video_data: bytes, language: str = "uz") -> Optional[str]:
        """
        Process video input: extract audio and convert to text
        
        Args:
            video_data: Video file bytes
            language: Language code for speech recognition
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Extract audio from video
            audio_bytes = await self.extract_audio_from_video(video_data)
            if not audio_bytes:
                return None
            
            # Convert speech to text
            text = await self.speech_to_text(audio_bytes, language)
            return text
            
        except Exception as e:
            logger.error(f"Video processing error: {str(e)}")
            return None


# Initialize audio service instance
audio_service = AudioService()
