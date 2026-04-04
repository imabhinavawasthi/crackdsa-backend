import requests
import json
import uuid

# Base URL - Assuming the server is running locally
BASE_URL = "http://localhost:8000/api/v1/dsa-sheets"

def test_dsa_sheets_crud():
    print("🚀 Starting DSA Sheets CRUD Verification...")

    # 1. Create a sheet
    sheet_id = f"test_sheet_{uuid.uuid4().hex[:8]}"
    payload = {
        "id": sheet_id,
        "title": "Test DSA Sheet",
        "description": "A sheet created for testing purposes",
        "tags": ["test", "dsa"],
        "level": "beginner",
        "estimated_hours": 10,
        "is_public": True,
        "sheet_json": {
            "topics": [
                {
                    "id": "arrays",
                    "title": "Arrays",
                    "steps": [
                        {
                            "id": "traversal",
                            "title": "Traversal",
                            "pattern_id": "traversal",
                            "problems": [
                                { "problem_id": "sum_of_array" }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    print(f"\n1. Creating sheet with id: {sheet_id}...")
    create_resp = requests.post(BASE_URL, json=payload)
    if create_resp.status_code == 200:
        print("✅ Sheet created successfully")
    else:
        print(f"❌ Failed to create sheet: {create_resp.status_code} - {create_resp.text}")
        return

    # 2. Get the sheet
    print(f"\n2. Retrieving sheet {sheet_id}...")
    get_resp = requests.get(f"{BASE_URL}/{sheet_id}")
    if get_resp.status_code == 200:
        data = get_resp.json()
        print(f"✅ Sheet retrieved: {data['title']}")
    else:
        print(f"❌ Failed to retrieve sheet: {get_resp.status_code}")
        return

    # 3. List sheets
    print("\n3. Listing all active sheets...")
    list_resp = requests.get(BASE_URL)
    if list_resp.status_code == 200:
        sheets = list_resp.json()
        print(f"✅ Found {len(sheets)} active sheets")
        if any(s['id'] == sheet_id for s in sheets):
            print("✅ Created sheet found in list")
        else:
            print("❌ Created sheet NOT found in list")
    else:
        print(f"❌ Failed to list sheets: {list_resp.status_code}")

    # 4. Update the sheet
    print(f"\n4. Updating sheet {sheet_id} title...")
    payload["title"] = "Updated Test DSA Sheet"
    update_resp = requests.put(f"{BASE_URL}/{sheet_id}", json=payload)
    if update_resp.status_code == 200:
        print("✅ Sheet updated successfully")
        print(f"   New Title: {update_resp.json()['title']}")
    else:
        print(f"❌ Failed to update sheet: {update_resp.status_code}")

    # 5. Soft delete the sheet
    print(f"\n5. Soft deleting sheet {sheet_id}...")
    del_resp = requests.delete(f"{BASE_URL}/{sheet_id}")
    if del_resp.status_code == 200:
        print("✅ Sheet soft deleted successfully")
    else:
        print(f"❌ Failed to delete sheet: {del_resp.status_code}")

    # 6. Verify it's gone from list/get
    print("\n6. Verifying sheet is no longer active...")
    final_get_resp = requests.get(f"{BASE_URL}/{sheet_id}")
    if final_get_resp.status_code == 404:
        print("✅ Sheet correctly returns 404 (Inactive/Not Found)")
    else:
        print(f"❌ Sheet still returns {final_get_resp.status_code}")

    print("\n🏁 CRUD Verification Complete!")

if __name__ == "__main__":
    # Note: This script requires the backend server to be running at localhost:8000
    try:
        test_dsa_sheets_crud()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server. Make sure it's running on port 8000.")
