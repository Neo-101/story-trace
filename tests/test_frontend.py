import requests

def test_frontend():
    print("Testing Frontend...")
    try:
        resp = requests.get("http://localhost:8000/")
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
