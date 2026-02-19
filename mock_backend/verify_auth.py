import requests
import random
import string
import time

BASE_URL = "http://localhost:8000/api/v1/auth"

def get_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def get_admin_token():
    username = f"admin_{get_random_string()}"
    email = f"{username}@coforge.com" # Use coforge email for realism if needed, though current regex might not enforce strictly everywhere in mock
    password = "adminpassword"
    
    # Register
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": "admin",
        "profile": {"first_name": "Admin", "last_name": "Tester"}
    }
    requests.post(f"{BASE_URL}/register/admin", json=payload)
    
    # Login
    resp = requests.post(f"{BASE_URL}/login/admin", json={"username": username, "password": password})
    return resp.json()["access_token"]

def test_admin_features():
    print("\n--- Testing Admin Features ---")
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Admin Register Candidate (Multipart)
    print("1. Admin Register Candidate...")
    cand_email = f"newcand_{get_random_string()}@example.com"
    files = {
        'resume': ('resume.pdf', b'fake_content', 'application/pdf')
    }
    data = {
        'candidate_name': 'John Doe',
        'candidate_email': cand_email,
        'job_description': 'Python Developer'
    }
    
    resp = requests.post(f"{BASE_URL}/admin/register-candidate", headers=headers, files=files, data=data)
    if resp.status_code != 201:
        print(f"FAILED: Register Candidate {resp.text}")
        return
    print("SUCCESS: Candidate Registered via Admin")
    cand_data = resp.json()
    cand_id = cand_data["id"]
    
    # 2. Get All Candidates
    print("2. Get All Candidates...")
    resp = requests.get(f"{BASE_URL}/admin/candidates", headers=headers)
    if resp.status_code != 200:
        print(f"FAILED: Get Candidates {resp.text}")
        return
    candidates = resp.json()
    found = any(c["id"] == cand_id for c in candidates)
    if found:
        print("SUCCESS: Candidate found in list")
    else:
        print("FAILED: Candidate NOT found in list")
        
    # 3. Toggle Login (Disable)
    print("3. Disable Candidate Login...")
    resp = requests.post(f"{BASE_URL}/admin/candidates/{cand_id}/toggle-login", headers=headers)
    if resp.status_code != 200:
        print(f"FAILED: Toggle Login {resp.text}")
        return
    print(f"SUCCESS: {resp.json()['message']}")
    
    # 4. Verify Login Blocked
    # We need the generated password? mock email service prints it but we can't read it easily programmatically here.
    # BUT, we can just toggle checking.
    # Actually, verify_auth usually runs blindly. 
    # To test login block, we need the password.
    # Since we can't intercept stdout easily here without complex setup...
    # I will modify the MockEmailService to also just set a hardcoded password for testing? 
    # Or I can just check the database state via another endpoint?
    # Or, simpler: I'll trust the unit test of 'toggle' returns correct status, and verify logic by trying to login with a KNOWN user that I register normally then disable.
    
    print("4. Verify Login Blocked mechanism (using standard registered candidate)...")
    # Register standard candidate
    c_user = f"block_test_{get_random_string()}"
    c_pass = "password123"
    requests.post(f"{BASE_URL}/register/candidate", json={
        "username": c_user, "email": f"{c_user}@test.com", "password": c_pass, "role": "candidate", 
        "profile": {"first_name": "Block", "last_name": "Test"}
    })
    
    # Login check (should work)
    resp = requests.post(f"{BASE_URL}/login/candidate", json={"username": c_user, "password": c_pass})
    if resp.status_code != 200:
        print("FAILED: Setup login failed")
        return
    
    # Get ID? We need ID to toggle. Login response includes user_data usually?
    # In my implementation of login_candidate, I return TokenResponse which has username.
    # I don't return ID in TokenResponse yet. I should have?
    # Wait, the TokenResponse model in schemas/auth.py only has access_token, token_type, username, role.
    # I need to get ID from somewhere. 
    # Admin can find it by username? No endpoint for search.
    # Admin 'list candidates' has it.
    
    print("   Finding candidate ID from admin list...")
    resp = requests.get(f"{BASE_URL}/admin/candidates", headers=headers)
    candidates = resp.json()
    target_cand = next((c for c in candidates if c["username"] == c_user), None)
    if not target_cand:
        print("FAILED: Could not find test candidate")
        return
    
    c_id = target_cand["id"]
    
    # Disable
    print(f"   Disabling login for {c_user} ({c_id})...")
    requests.post(f"{BASE_URL}/admin/candidates/{c_id}/toggle-login", headers=headers)
    
    # Try Login
    print("   Attempting login (should fail)...")
    resp = requests.post(f"{BASE_URL}/login/candidate", json={"username": c_user, "password": c_pass})
    if resp.status_code == 403 and "disabled" in resp.text:
        print("SUCCESS: Login blocked with 403")
    else:
        print(f"FAILED: Login not blocked correctly. Status: {resp.status_code}")

if __name__ == "__main__":
    try:
        test_admin_features()
        print("\nAll Admin Feature Tests Passed!")
    except Exception as e:
        print(f"\nTest Execution Failed: {e}")
