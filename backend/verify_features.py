import urllib.request
import urllib.parse
import json
import ssl
import sys

BASE_URL = "http://localhost:8000/api"

# Bypass SSL verification if needed (for localhost sometimes)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
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
                try:
                    return status, json.loads(body)
                except:
                    return status, body
            return status, None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, body
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def login(username, password):
    url = f"{BASE_URL}/auth/token"
    # Token endpoint expects form data, not JSON usually? FastAPI OAuth2PasswordRequestForm
    # Wait, in the code it's probably Form data.
    # Let's check auth.py or just try form data.
    # Usually `username=...&password=...`
    
    data = urllib.parse.urlencode({'username': username, 'password': password}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method="POST")
    # req.add_header('Content-Type', 'application/x-www-form-urlencoded') # Default
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            body = json.loads(response.read().decode('utf-8'))
            return body["access_token"]
    except urllib.error.HTTPError as e:
        print(f"Login failed: {e.read().decode('utf-8')}")
        return None

def verify_delete_stock():
    print("\n--- Testing Delete Stock ---")
    
    # 1. Register/Login Owner
    owner_data = {
        "full_name": "Test Owner",
        "username": "test_owner_del",
        "password": "password123",
        "business_name": "Test Corp",
        "business_type": "Retail",
        "email": "owner.del@test.com",
        "role": "owner"
    }
    
    token = login(owner_data["username"], owner_data["password"])
    if not token:
        print("Registering new owner...")
        status, _ = make_request(f"{BASE_URL}/auth/register", "POST", owner_data)
        if status != 200:
            print("Registration failed.")
            return
        token = login(owner_data["username"], owner_data["password"])
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add Stock
    stock_item = {
        "product_name": "Delete Me",
        "company_name": "Test Corp",
        "category": "Test",
        "quantity": 10
    }
    status, res = make_request(f"{BASE_URL}/stock/add-or-update", "POST", stock_item, headers)
    if status != 200:
        print(f"Failed to add stock: {res}")
        return
    
    stock_id = res["id"]
    print(f"Created stock item ID: {stock_id}")
    
    # 3. Delete Stock
    status, _ = make_request(f"{BASE_URL}/stock/{stock_id}", "DELETE", headers=headers)
    if status == 204:
        print("✅ Delete Success (Owner)")
    else:
        print(f"❌ Delete Failed: {status} - {_}")

    # 4. Verify Gone
    status, items = make_request(f"{BASE_URL}/stock/list", "GET", headers=headers)
    if any(item["id"] == stock_id for item in items):
         print("❌ Item still exists in list!")
    else:
         print("✅ Item confirmed deleted")

def verify_staff_email():
    print("\n--- Testing Staff Creation with Email ---")
    owner_username = "test_owner_del"
    token = login(owner_username, "password123")
    if not token:
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    staff_data = {
        "staff_name": "Test Staff Email",
        "email": "test_staff@example.com"
    }
    
    status, res = make_request(f"{BASE_URL}/staff/create", "POST", staff_data, headers)
    if status == 200:
        print("✅ Staff Created with Email Success")
        print(f"Staff Creds: {res['username']}")
    else:
        print(f"❌ Staff Creation Failed: {status} - {res}")

if __name__ == "__main__":
    verify_delete_stock()
    verify_staff_email()
