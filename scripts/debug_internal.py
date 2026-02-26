import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.getcwd())

print(f"Working Directory: {os.getcwd()}")

try:
    print("Importing app from backend.server...")
    from backend.server import app
    
    print("\n=== Route Table Check ===")
    found_novels = False
    for route in app.routes:
        methods = getattr(route, "methods", None)
        print(f"Path: {route.path:<30} | Name: {route.name:<20} | Methods: {methods}")
        if route.path == "/api/novels" or route.path == "/api/novels/":
            found_novels = True
            
    if not found_novels:
        print("\n❌ CRITICAL: /api/novels route is MISSING from app.routes!")
    else:
        print("\n✅ Route /api/novels is registered correctly.")

    print("\n=== Simulation Test ===")
    client = TestClient(app)
    
    # Test 1: Root
    print("Requesting GET / ... ", end="")
    resp = client.get("/")
    print(f"Status: {resp.status_code}")
    
    # Test 2: Novels
    print("Requesting GET /api/novels ... ", end="")
    resp = client.get("/api/novels")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response: {resp.json()}")
    else:
        print(f"Error: {resp.text}")

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("This usually means missing __init__.py files or wrong PYTHONPATH.")
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
