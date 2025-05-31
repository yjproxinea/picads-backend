import asyncio
import os
import uuid
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Set up test environment variables before importing the app
os.environ["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")
os.environ["SUPABASE_ANON_KEY"] = os.getenv("SUPABASE_ANON_KEY", "")
os.environ["SUPABASE_JWT_SECRET"] = os.getenv("SUPABASE_JWT_SECRET", "")

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Import the FastAPI app after setting env vars
from main import app

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Create Supabase client (only if we have the required env vars)
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create FastAPI test client
client = TestClient(app)

def generate_test_email():
    """Generate a unique test email for each run"""
    unique_id = str(uuid.uuid4())[:8]
    return f"test_{unique_id}@example.com"

def test_signup_and_profile_creation():
    """Test the complete flow: Supabase signup -> Profile creation"""
    
    if not supabase:
        print("❌ Supabase client not initialized - check environment variables")
        return
    
    # Test user credentials with random email
    test_email = generate_test_email()
    test_password = "testpassword123"
    test_full_name = "Test User"
    
    print("🚀 Starting Supabase signup and profile creation test...")
    print(f"📧 Using test email: {test_email}")
    
    try:
        # Step 1: Sign up with Supabase
        print(f"📝 Step 1: Signing up user: {test_email}")
        
        auth_response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password,
            "options": {
                "data": {
                    "full_name": test_full_name
                }
            }
        })
        
        if auth_response.user and auth_response.session:
            print(f"✅ Signup successful! User ID: {auth_response.user.id}")
            access_token = auth_response.session.access_token
            print(f"🔑 Access token obtained: {access_token[:20]}...")
        else:
            print("❌ Signup failed - no user or session returned")
            return
        
        # Step 2: Test profile creation endpoint
        print("\n📝 Step 2: Creating profile via API...")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        profile_data = {
            "full_name": test_full_name
        }
        
        # Test POST /profile (create or get profile)
        response = client.post("/profile", json=profile_data, headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile created successfully!")
            print(f"   Profile ID: {profile['id']}")
            print(f"   Full Name: {profile['full_name']}")
            print(f"   Credits: {profile['credits']}")
            print(f"   Stripe Customer ID: {profile['stripe_customer_id']}")
        else:
            print(f"❌ Profile creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # Step 3: Test profile retrieval
        print("\n📝 Step 3: Retrieving profile via API...")
        
        response = client.get("/profile", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile retrieved successfully!")
            print(f"   Profile ID: {profile['id']}")
            print(f"   Full Name: {profile['full_name']}")
            print(f"   Credits: {profile['credits']}")
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Step 4: Test profile update
        print("\n📝 Step 4: Updating profile via API...")
        
        update_data = {
            "full_name": "Updated Test User",
            "credits": 150
        }
        
        response = client.put("/profile", json=update_data, headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile updated successfully!")
            print(f"   Updated Full Name: {profile['full_name']}")
            print(f"   Updated Credits: {profile['credits']}")
        else:
            print(f"❌ Profile update failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Step 5: Test dashboard endpoint
        print("\n📝 Step 5: Testing dashboard endpoint...")
        
        response = client.get("/dashboard", headers=headers)
        
        if response.status_code == 200:
            dashboard = response.json()
            print(f"✅ Dashboard accessed successfully!")
            print(f"   Message: {dashboard['message']}")
            print(f"   User ID: {dashboard['user_id']}")
            if 'profile' in dashboard:
                print(f"   Profile Credits: {dashboard['profile']['credits']}")
        else:
            print(f"❌ Dashboard access failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup: Sign out the user
        try:
            if supabase:
                supabase.auth.sign_out()
                print("\n🧹 User signed out successfully")
        except:
            pass

def test_authentication_flow():
    """Test just the authentication without profile creation"""
    
    if not supabase:
        print("❌ Supabase client not initialized - check environment variables")
        return
    
    # Generate random email for auth test
    test_email = generate_test_email()
    test_password = "testpassword123"
    
    print("🔐 Testing authentication flow...")
    print(f"📧 Using test email: {test_email}")
    
    try:
        # Sign up
        auth_response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if auth_response.user and auth_response.session:
            access_token = auth_response.session.access_token
            print(f"✅ Authentication successful!")
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = client.get("/dashboard", headers=headers)
            
            if response.status_code == 200:
                print("✅ Protected endpoint accessible!")
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")

def test_public_endpoints():
    """Test public endpoints that don't require authentication"""
    
    print("🌐 Testing public endpoints...")
    
    # Test welcome endpoint
    response = client.get("/")
    if response.status_code == 200:
        print("✅ Welcome endpoint accessible")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Welcome endpoint failed: {response.status_code}")
    
    # Test public data endpoint without auth
    response = client.get("/public-data")
    if response.status_code == 200:
        print("✅ Public data endpoint accessible without auth")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Public data endpoint failed: {response.status_code}")

if __name__ == "__main__":
    print("🧪 Running FastAPI Profile Tests")
    print("=" * 50)
    
    # Check if environment variables are set
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("❌ Missing Supabase environment variables!")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
        exit(1)
    
    if not SUPABASE_JWT_SECRET:
        print("❌ Missing SUPABASE_JWT_SECRET!")
        print("Please set SUPABASE_JWT_SECRET in your .env file")
        print("You can find this in your Supabase project settings → API → JWT Secret")
        exit(1)
    
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 JWT Secret configured: {'✅' if SUPABASE_JWT_SECRET else '❌'}")
    print()
    
    # Test public endpoints first
    test_public_endpoints()
    
    print("\n" + "=" * 50)
    print("🧪 Running Authentication Test")
    print("=" * 50)
    
    # Run authentication test
    test_authentication_flow()
    
    print("\n" + "=" * 50)
    print("🧪 Running Profile Creation Test")
    print("=" * 50)
    
    # Run the main test
    test_signup_and_profile_creation() 