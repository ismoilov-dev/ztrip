#!/usr/bin/env python3
"""
WebSocket test script for AI Audio Guide
"""

import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection and messages"""
    
    # Replace with your actual JWT token
    token = "your_jwt_token_here"
    uri = f"ws://localhost:8000/ws/live-guide/?token={token}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test location setting
            await websocket.send(json.dumps({
                "type": "set_location",
                "location_id": "1"
            }))
            print("📍 Sent location setting")
            
            # Listen for responses
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received: {data['type']} - {data.get('message', '')}")
                
                # After location is set, send a test question
                if data['type'] == 'location_set':
                    await websocket.send(json.dumps({
                        "type": "question",
                        "text": "Bu yer haqida qisqacha ma'lumot bering"
                    }))
                    print("🎤 Sent test question")
                    
                # Stop after receiving answer
                if data['type'] in ['answer', 'audio_answer']:
                    print("✅ Test completed successfully!")
                    break
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure:")
        print("   - Server is running (python manage.py runserver)")
        print("   - Replace 'your_jwt_token_here' with actual JWT token")
        print("   - User has valid authentication")

if __name__ == "__main__":
    asyncio.run(test_websocket())
