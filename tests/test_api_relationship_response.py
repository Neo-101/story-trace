import os

# ... imports ...

def test_relationship_api():
    print("Testing Relationship API...")
    
    port = "8000"
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("API_PORT="):
                    port = line.split("=")[1].strip()
                    break

    # ... get session ...
    
    # 2. Call API
    url = f"http://localhost:{port}/api/novels/{novel.name}/{file_hash}/{timestamp}/relationship"
    params = {
        "source": "孙杰克",
        "target": "宋6PUS"
    }
    
    try:
        print(f"GET {url}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        print(f"Received {len(data)} events.")
        
        has_state = False
        for event in data:
            if event.get("narrative_state"):
                has_state = True
                print(f"✅ Found state in Chapter {event.get('chapter_index', 'Unknown')}")
                # Print one for inspection
                print(json.dumps(event["narrative_state"], indent=2, ensure_ascii=False))
                break
        
        if not has_state:
            print("❌ No narrative_state found in any event.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_relationship_api()
