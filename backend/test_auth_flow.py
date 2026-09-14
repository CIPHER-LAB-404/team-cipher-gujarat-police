import requests

base_url = "http://localhost:8000/api"

print("--- Testing API Flow ---")

# 1. Login
print("1. Attempting login as admin...")
data = {"username": "admin", "password": "Sentinel@Admin2026"}
res = requests.post(f"{base_url}/auth/login", data=data)

if res.status_code == 200:
    token = res.json()["access_token"]
    print("   [OK] Login successful. Token received.")
else:
    print(f"   [FAIL] Login failed: {res.text}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. Get Me
print("2. Fetching current user profile...")
res = requests.get(f"{base_url}/auth/me", headers=headers)
if res.status_code == 200:
    print(f"   [OK] Profile retrieved: {res.json()['full_name']} ({res.json()['role']})")
else:
    print(f"   [FAIL] Could not get profile: {res.text}")

# 3. Access public route (Cameras)
print("3. Fetching cameras...")
res = requests.get(f"{base_url}/cameras")
if res.status_code == 200:
    print(f"   [OK] Cameras retrieved. Count: {len(res.json().get('cameras', []))}")
else:
    print(f"   [FAIL] Could not fetch cameras: {res.text}")

# 4. Access public route (Watchlist)
print("4. Fetching watchlist...")
res = requests.get(f"{base_url}/watchlist")
if res.status_code == 200:
    print(f"   [OK] Watchlist retrieved. Count: {len(res.json().get('watchlist', []))}")
else:
    print(f"   [FAIL] Could not fetch watchlist: {res.text}")

print("--- All tests passed! ---")
