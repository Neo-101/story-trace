import sys
import os

# Set up PYTHONPATH like main.py
sys.path.append(os.getcwd())

print(f"Current Directory: {os.getcwd()}")
print(f"sys.path[0]: {sys.path[0]}")

try:
    print("Attempting to import backend.server...")
    from backend.server import app
    print("✅ Successfully imported backend.server")
    
    print("\n=== Registered Routes (Checking app object) ===")
    route_paths = []
    for route in app.routes:
        print(f"Path: {route.path} | Name: {route.name} | Methods: {route.methods}")
        route_paths.append(route.path)
    print("=========================")
    
    if "/api/novels" in route_paths or "/api/novels/" in route_paths:
        print("✅ Route /api/novels found!")
    else:
        print("❌ Route /api/novels NOT found!")

except Exception as e:
    print(f"❌ Failed to import backend.server: {e}")
    import traceback
    traceback.print_exc()
