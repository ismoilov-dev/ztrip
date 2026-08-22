#!/usr/bin/env python3
"""
Test script for /coin/add-xp endpoint
Shows how to properly send request body with XP amount
"""

import requests
import json

def test_add_xp():
    """Test the add-xp endpoint with proper authentication"""
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    endpoint = "/coin/add-xp/"
    
    # You need to get a valid JWT token first
    # Option 1: Get token from login
    login_data = {
        "email": "your_email@example.com",  # Replace with actual email
        "password": "your_password"          # Replace with actual password
    }
    
    try:
        # Step 1: Login to get token
        login_response = requests.post(
            f"{base_url}/api/auth/token/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get('access')
            print(f"✅ Login successful! Token: {token[:20]}...")
            
            # Step 2: Test add-xp endpoint
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Test with different XP amounts
            test_cases = [
                {"xp": 1},
                {"xp": 50}, 
                {"xp": 100},
                {"xp": -5},  # Should fail
                {"xp": 0},   # Should fail
                {"xp": "abc"} # Should fail
            ]
            
            for i, test_data in enumerate(test_cases, 1):
                print(f"\n--- Test Case {i}: {test_data} ---")
                
                response = requests.post(
                    f"{base_url}{endpoint}",
                    json=test_data,
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure server is running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing /coin/add-xp endpoint")
    print("=" * 50)
    print("Instructions:")
    print("1. Replace email/password with actual credentials")
    print("2. Run script: python test_add_xp.py")
    print("=" * 50)
    
    test_add_xp()
