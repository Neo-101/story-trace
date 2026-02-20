import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("Testing API...")
    
    # 1. List Novels
    print("\n[GET] /novels")
    try:
        resp = requests.get(f"{BASE_URL}/novels")
        print(f"Status: {resp.status_code}")
        novels = resp.json()
        print(f"Response: {json.dumps(novels, indent=2, ensure_ascii=False)}")
        
        if not novels:
            print("No novels found, skipping further tests.")
            return

        novel_name = novels[0]['name']
        file_hash = novels[0]['hashes'][0]
        
        # 2. List Runs
        print(f"\n[GET] /novels/{novel_name}/{file_hash}/runs")
        resp = requests.get(f"{BASE_URL}/novels/{novel_name}/{file_hash}/runs")
        print(f"Status: {resp.status_code}")
        runs = resp.json()
        # print(f"Response: {json.dumps(runs, indent=2, ensure_ascii=False)}")
        
        if not runs:
            print("No runs found, skipping further tests.")
            return

        timestamp = runs[0]['timestamp']
        print(f"Using run: {timestamp}")

        # 3. List Chapters
        print(f"\n[GET] /novels/{novel_name}/{file_hash}/{timestamp}/chapters")
        resp = requests.get(f"{BASE_URL}/novels/{novel_name}/{file_hash}/{timestamp}/chapters")
        print(f"Status: {resp.status_code}")
        chapters = resp.json()
        print(f"Found {len(chapters)} chapters")
        # print(f"Response: {json.dumps(chapters[:2], indent=2, ensure_ascii=False)}")
        
        if not chapters:
            print("No chapters found, skipping detail test.")
            return
            
        chapter_id = chapters[0]['id']
        
        # 4. Get Chapter Detail
        print(f"\n[GET] /novels/{novel_name}/{file_hash}/{timestamp}/chapters/{chapter_id}")
        resp = requests.get(f"{BASE_URL}/novels/{novel_name}/{file_hash}/{timestamp}/chapters/{chapter_id}")
        print(f"Status: {resp.status_code}")
        detail = resp.json()
        print(f"Title: {detail.get('title')}")
        print(f"Content Length: {len(detail.get('content', ''))}")
        print(f"Summary Count: {len(detail.get('summary_sentences', []))}")
        
        # Check source spans
        if detail.get('summary_sentences'):
            first_summary = detail['summary_sentences'][0]
            print(f"First Summary: {first_summary.get('summary_text')}")
            print(f"Source Spans: {first_summary.get('source_spans')}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_api()
