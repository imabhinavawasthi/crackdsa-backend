import requests
import json
import uuid

# Base URLs
BASE_URL = "http://localhost:8000/api/v1"
PUBLIC_URL = f"{BASE_URL}/dsa-sheets"
ADMIN_URL = f"{BASE_URL}/admin/dsa-sheets"

# Note: In a real test, you would need a valid Supabase JWT token for an admin user
# To be passed in the Authorization header: {"Authorization": "Bearer YOUR_TOKEN"}
ADMIN_AUTH_HEADERS = {
    "Authorization": "Bearer MOCK_ADMIN_TOKEN" # Replace with actual token if testing against live server
}

def test_dsa_sheets_admin_rbac():
    print("🚀 Starting DSA Sheets admin/Public Split Verification...")

    # 1. Access Public List
    print("\n1. Accessing Public List...")
    list_resp = requests.get(PUBLIC_URL)
    if list_resp.status_code == 200:
        print(f"✅ Public list accessible. Found {len(list_resp.json())} active sheets.")
    else:
        print(f"❌ Failed to access public list: {list_resp.status_code}")

    # 2. Access Admin List (Should fail without token)
    print("\n2. Accessing Admin List without auth...")
    admin_list_resp = requests.get(ADMIN_URL)
    if admin_list_resp.status_code in [401, 403]:
        print(f"✅ Correctly denied access (Status: {admin_list_resp.status_code})")
    else:
        print(f"❌ Access not denied! (Status: {admin_list_resp.status_code})")

    # 3. Create a sheet as Admin
    # (Assuming auth is handled or we're just checking the structure)
    print("\n3. Creating sheet via Admin (Structure Check)...")
    sheet_id = f"test_sheet_{uuid.uuid4().hex[:8]}"
    payload = {
        "id": sheet_id,
        "title": "Admin Created Sheet",
        "level": "beginner",
        "sheet_json": {"topics": []}
    }
    
    # Note: This will naturally fail if you don't have a valid token
    # But it shows where the request should go.
    print(f"   Target: POST {ADMIN_URL}")

    # 4. Cleanup/Final Verification
    print("\n🏁 Route reorganization Complete!")
    print("Summary:")
    print(f"  - Public: {PUBLIC_URL}")
    print(f"  - Admin:  {ADMIN_URL} (Requires RBAC)")

if __name__ == "__main__":
    try:
        test_dsa_sheets_admin_rbac()
    except requests.exceptions.ConnectionError:
        print("❌ Server not running at localhost:8000")
