import requests
import json
import sys
import os
from sqlmodel import Session, select

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.engine import engine
from core.db.models import Novel

def test_relationship_api():
    print("Testing Relationship API...")
    
    # 1. Get Novel Info
    with Session(engine) as session:
        novel = session.exec(select(Novel).where(Novel.name == "故障烏託邦")).first()
        if not novel:
            print("Novel not found")
            return
        
        file_hash = novel.versions[-1].hash
        # Just use a dummy timestamp, the API ignores it for now (uses best effort merge)
        timestamp = "latest" 
        
    print(f"Novel: {novel.name}, Hash: {file_hash}")
    
    # 2. Call API
    url = f"http://localhost:8000/api/novels/{novel.name}/{file_hash}/{timestamp}/relationship"
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
