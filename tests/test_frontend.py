import requests

def test_frontend():
    import os
    port = "8000"
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("API_PORT="):
                    port = line.split("=")[1].strip()
                    break

    print(f"Testing Frontend (Backend port: {port})...")
    try:
        resp = requests.get(f"http://localhost:{port}/")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            content = resp.text
            if "StoryTrace Visualization" in content and "Vue" in content:
                print("Frontend HTML served successfully!")
            else:
                print("Frontend HTML content unexpected.")
                print(content[:200])
        else:
            print("Failed to get /")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_frontend()
