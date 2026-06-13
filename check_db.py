from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
if url and key:
    supabase: Client = create_client(url, key)
    res = supabase.table("user_roadmaps").select("id, title").limit(1).execute()
    print("Roadmap found:", res.data)
    if res.data:
        rid = res.data[0]['id']
        up = supabase.table("user_roadmaps").update({"title": "TEST_TITLE"}).eq("id", rid).execute()
        print("Update result:", up.data)
else:
    print("No env vars")
