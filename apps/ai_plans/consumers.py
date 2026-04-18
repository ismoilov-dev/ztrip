import json
import os
import google.generativeai as genai
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import AIPlan, AIPlanStatus
from .audio_service import audio_service
from apps.location.models import Location
from django.conf import settings


class LiveGuideConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        query_string = self.scope.get("query_string", b"").decode()
        token = None
        for param in query_string.split("&"):
            if param.startswith("token="):
                token = param.replace("token=", "")
                break

        if not token:
            await self.close(code=4001)
            return

        try:
            access_token = AccessToken(token)
            user_id      = access_token["user_id"]
            self.user    = await get_user_model().objects.aget(id=user_id)
        except Exception:
            await self.close(code=4001)
            return

        self.location_context = ""
        self.chat             = None
        self.model            = None
        self.audio_language   = "uz"  # Default language for audio processing

        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=(
                    "Sen ZTrip AI audio guidsan. "
                    "Foydalanuvchi turistik joy haqida savol beradi. "
                    "Qisqa, aniq va qiziqarli javob ber (2-3 jumla). "
                    "O'zbek, Rus yoki Ingliz tilida javob ber."
                )
            )
            self.chat = self.model.start_chat(history=[])

        await self.accept()
        await self.send(json.dumps({
            "type":    "connected",
            "message": "AI Guide tayyor! Location yuborish uchun set_location yuboring.",
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "set_location":
            if not self.model:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "GEMINI_API_KEY sozlanmagan.",
                }))
                return

            location_id = data.get("location_id")
            location    = await self.get_location(location_id)

            if not location:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Location topilmadi.",
                }))
                return

            self.location_context = (
                f"Hozirgi joy: {location['name']}, {location['city']}. "
                f"Turi: {location['type']}. "
                f"Ma'lumot: {location['description']}"
            )
            self.chat = self.model.start_chat(history=[])

            await self.send(json.dumps({
                "type":     "location_set",
                "message":  f"{location['name']} uchun AI Guide tayyor!",
                "location": location,
            }))

        elif msg_type == "question":
            if not self.chat:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Avval set_location yuboring.",
                }))
                return

            question = data.get("text", "").strip()
            if not question:
                return

            await self.send(json.dumps({"type": "thinking"}))

            prompt = question
            if self.location_context:
                prompt = f"{self.location_context}\n\nSavol: {question}"

            try:
                response = await self.ask_gemini(prompt)
                await self.send(json.dumps({
                    "type": "answer",
                    "text": response,
                }))
            except Exception as e:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": f"Xatolik: {str(e)}",
                }))

        elif msg_type == "voice_question":
            if not self.chat:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Avval set_location yuboring.",
                }))
                return

            audio_data = data.get("audio", "")
            language = data.get("language", "uz")
            self.audio_language = language

            if not audio_data:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Audio ma'lumotlari yo'q.",
                }))
                return

            await self.send(json.dumps({"type": "processing_voice"}))

            try:
                # Decode audio data
                audio_bytes = audio_service.decode_base64_audio(audio_data)
                if not audio_bytes:
                    raise Exception("Audio dekoding xatolik")

                # Convert speech to text
                text = await audio_service.speech_to_text(audio_bytes, language)
                if not text:
                    raise Exception("Ovozni matnga aylantirib bo'lmadi")

                # Send transcribed text to user
                await self.send(json.dumps({
                    "type": "transcribed",
                    "text": text,
                }))

                # Get AI response
                await self.send(json.dumps({"type": "thinking"}))
                
                prompt = text
                if self.location_context:
                    prompt = f"{self.location_context}\n\nSavol: {text}"

                response = await self.ask_gemini(prompt)
                
                # Convert response to speech
                await self.send(json.dumps({"type": "generating_audio"}))
                audio_response = await audio_service.text_to_speech(response, language)
                
                if audio_response:
                    audio_base64 = audio_service.encode_base64_audio(audio_response)
                    await self.send(json.dumps({
                        "type": "audio_answer",
                        "text": response,
                        "audio": audio_base64,
                        "language": language,
                    }))
                else:
                    # Fallback to text only
                    await self.send(json.dumps({
                        "type": "answer",
                        "text": response,
                    }))

            except Exception as e:
                error_msg = str(e)
                
                # Check for quota exceeded
                if "quota" in error_msg.lower() and "exceeded" in error_msg.lower():
                    fallback_response = (
                        "Kechirasiz, API limitiga yetib boldik. "
                        "Iltimos, birozdan so'ng yana urinib ko'ring. "
                        "Agar muammo davom etsa, administrator bilan bog'laning."
                    )
                    
                    # Try to generate audio response for fallback
                    try:
                        audio_response = await audio_service.text_to_speech(fallback_response, self.audio_language)
                        if audio_response:
                            audio_base64 = audio_service.encode_base64_audio(audio_response)
                            await self.send(json.dumps({
                                "type": "quota_exceeded",
                                "text": fallback_response,
                                "audio": audio_base64,
                                "language": self.audio_language,
                            }))
                        else:
                            await self.send(json.dumps({
                                "type": "quota_exceeded", 
                                "text": fallback_response,
                            }))
                    except:
                        await self.send(json.dumps({
                            "type": "quota_exceeded",
                            "text": fallback_response,
                        }))
                else:
                    await self.send(json.dumps({
                        "type":    "error",
                        "message": f"Ovozli javob xatolik: {error_msg}",
                    }))

        elif msg_type == "set_language":
            language = data.get("language", "uz")
            if language in ["uz", "ru", "en"]:
                self.audio_language = language
                await self.send(json.dumps({
                    "type": "language_set",
                    "language": language,
                    "message": f"Til o'zgartirildi: {language}",
                }))
            else:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Qo'llab-quvvatlanmaydigan til. Faqat uz, ru, en.",
                }))

        elif msg_type == "video_question":
            if not self.chat:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Avval set_location yuboring.",
                }))
                return

            video_data = data.get("video", "")
            language = data.get("language", "uz")
            self.audio_language = language

            if not video_data:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "Video ma'lumotlari yo'q.",
                }))
                return

            await self.send(json.dumps({"type": "processing_video"}))

            try:
                # Decode video data
                video_bytes = audio_service.decode_base64_video(video_data)
                if not video_bytes:
                    raise Exception("Video dekoding xatolik")

                # Process video: extract audio and convert to text
                text = await audio_service.process_video_input(video_bytes, language)
                if not text:
                    raise Exception("Videodan ovozni matnga aylantirib bo'lmadi")

                # Send transcribed text to user
                await self.send(json.dumps({
                    "type": "video_transcribed",
                    "text": text,
                }))

                # Get AI response
                await self.send(json.dumps({"type": "thinking"}))
                
                prompt = text
                if self.location_context:
                    prompt = f"{self.location_context}\n\nVideo savol: {text}"

                response = await self.ask_gemini(prompt)
                
                # Convert response to speech
                await self.send(json.dumps({"type": "generating_audio"}))
                audio_response = await audio_service.text_to_speech(response, language)
                
                if audio_response:
                    audio_base64 = audio_service.encode_base64_audio(audio_response)
                    await self.send(json.dumps({
                        "type": "video_answer",
                        "text": response,
                        "audio": audio_base64,
                        "language": language,
                    }))
                else:
                    # Fallback to text only
                    await self.send(json.dumps({
                        "type": "answer",
                        "text": response,
                    }))

            except Exception as e:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": f"Video javob xatolik: {str(e)}",
                }))

        elif msg_type == "generate_plan":
            city     = data.get("city")
            days     = data.get("days", 3)
            budget   = data.get("budget", 0)
            language = data.get("language", "uz")

            if not city:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": "city yuborish shart.",
                }))
                return

            is_prem = await self.check_premium()
            if not is_prem:
                count = await self.get_today_count()
                if count >= 3:
                    await self.send(json.dumps({
                        "type":    "error",
                        "message": "Kunlik limit 3ta. Premium oling.",
                    }))
                    return

            await self.send(json.dumps({
                "type":    "generating",
                "message": f"{city} uchun marshrut yaratilmoqda...",
            }))

            try:
                plan = await self.create_plan(city, days, budget, language)
                await self.send(json.dumps({
                    "type":    "plan_ready",
                    "plan_id": plan["id"],
                    "city":    plan["city"],
                    "days":    plan["days"],
                    "message": "Marshrut tayyor!",
                }))
            except Exception as e:
                await self.send(json.dumps({
                    "type":    "error",
                    "message": str(e),
                }))

    @sync_to_async
    def get_location(self, location_id):
        loc = Location.objects.filter(id=location_id).first()
        if not loc:
            return None
        return {
            "id":          loc.id,
            "name":        loc.name,
            "city":        loc.city,
            "type":        loc.get_type_display(),
            "description": loc.description or "",
        }

    @sync_to_async
    def check_premium(self):
        return self.user.subscriptions.filter(
            plan="premium", is_active=True,
        ).exists()

    @sync_to_async
    def get_today_count(self):
        return AIPlan.objects.filter(
            user=self.user,
            created_at__date=timezone.now().date(),
        ).count()

    @sync_to_async
    def create_plan(self, city, days, budget, language):
        from .prompt import get_locations, travel_planner_prompt, TRAVEL_PLANNER_SYSTEM
        from .ai_client import call_ai

        locs   = get_locations(city, [])
        user_p = travel_planner_prompt(
            city=city, days=days,
            budget=budget, interests=[],
            language=language, locations=locs,
        )
        plan_json, model = call_ai(
            TRAVEL_PLANNER_SYSTEM, user_p, max_tokens=2500
        )
        plan = AIPlan.objects.create(
            user=self.user,
            city=city, days=days, budget=budget,
            status=AIPlanStatus.COMPLETED,
            plan_json=plan_json,
            ai_model_used=model,
            prompt_used=user_p,
        )
        return {"id": plan.id, "city": plan.city, "days": plan.days}

    async def ask_gemini(self, prompt: str) -> str:
        response = await self.chat.send_message_async(prompt)
        return response.text