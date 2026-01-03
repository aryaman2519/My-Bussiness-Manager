import urllib.request
import urllib.parse
import json
import ssl
import sys
import time

BASE_URL = "http://localhost:8000/api"

# Bypass SSL
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def make_request(url, method="GET", data=None, headers=None):
    if headers is None: headers = {}
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = None
    
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status = response.status
            body = response.read().decode('utf-8')
            if body:
                try: return status, json.loads(body)
                except: return status, body
            return status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def scenario_fresh_start():
    print("\n--- Testing Strict Deletion & Fresh Start ---")
    
    # 1. Register Owner
    user_unique = f"owner_{int(time.time())}"
    owner_data = {
        "full_name": "Test Deleter",
        "username": user_unique,
        "password": "password123",
        "business_name": "Delete Corp",
        "business_type": "Retail",
        "email": f"{user_unique}@test.com",
        "role": "owner"
    }
    
    print(f"1. Registering {user_unique}...")
    s, r = make_request(f"{BASE_URL}/auth/register", "POST", owner_data)
    if s != 200:
        print(f"Failed to register: {r}")
        return
        
    # Login
    login_data = urllib.parse.urlencode({'username': user_unique, 'password': 'password123'}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/token", data=login_data, method="POST")
    with urllib.request.urlopen(req, context=ctx) as resp:
        token = json.loads(resp.read().decode())["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add Data (Stock & Staff)
    print("2. Adding Data (Stock & Staff)...")
    
    # Add Stock
    stock_item = {
        "product_name": "To Be Deleted",
        "company_name": "Delete Corp",
        "category": "Test",
        "quantity": 100
    }
    s, _ = make_request(f"{BASE_URL}/stock/add-or-update", "POST", stock_item, headers)
    if s != 200: print(f"Stock add failed: {_}")
    
    # Add Staff
    staff_data = {
        "staff_name": "Staff Victim",
        "email": f"staff_{user_unique}@test.com"
    }
    s, staff_res = make_request(f"{BASE_URL}/staff/create", "POST", staff_data, headers)
    if s != 200: print(f"Staff add failed: {staff_res}")
    
    # 3. Delete Account
    print("3. Deleting Account...")
    s, _ = make_request(f"{BASE_URL}/auth/me", "DELETE", headers=headers)
    if s == 204:
        print("✅ Account Deleted")
    else:
        print(f"❌ Delete Failed: {s} - {_}")
        return

    # 4. Verify Fresh Start (Re-register same data)
    print("4. Verifying Fresh Start (Re-registering)...")
    s, r = make_request(f"{BASE_URL}/auth/register", "POST", owner_data)
    if s == 200:
         print("✅ Re-registration Success (Clean Slate)")
    else:
         print(f"❌ Re-registration Failed (Old data persists?): {s} - {r}")
         return

    # Login Again
    login_data = urllib.parse.urlencode({'username': user_unique, 'password': 'password123'}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/token", data=login_data, method="POST")
    with urllib.request.urlopen(req, context=ctx) as resp:
        new_token = json.loads(resp.read().decode())["access_token"]
    
    new_headers = {"Authorization": f"Bearer {new_token}"}
    
    # Check Inventory (Should be empty)
    s, items = make_request(f"{BASE_URL}/stock/list", "GET", headers=new_headers)
    if len(items) == 0:
        print("✅ Inventory Empty (Fresh Start Confirmed)")
    else:
        print(f"❌ Inventory Persists! Found {len(items)} items.")

    # Check Staff (Should be empty)
    s, staff = make_request(f"{BASE_URL}/staff/list", "GET", headers=new_headers)
    if len(staff) == 0:
        print("✅ Staff List Empty (Fresh Start Confirmed)")
    else:
        print(f"❌ Staff Persists! Found {len(staff)} members.")

if __name__ == "__main__":
    try:
        scenario_fresh_start()
    except Exception as e:
        print(f"Test crashed: {e}")
