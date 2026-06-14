import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TEST_TOKEN") or os.getenv("ADMIN_TOKEN")
if not token:
    print("No token")
    # try reading from .env manually
    with open(".env") as f:
        for line in f:
            if line.startswith("TEST_TOKEN="):
                token = line.split("=", 1)[1].strip()

headers = {"Authorization": f"Bearer {token}"}
print("Token:", token[:10] if token else "None")
r = requests.get("http://localhost:8000/api/v1/admin/courses/", headers=headers)
print("Status:", r.status_code)
print("Response:", r.text[:1000])
