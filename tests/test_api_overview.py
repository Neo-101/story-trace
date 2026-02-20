import os
import json
import pytest
from fastapi.testclient import TestClient
from web_ui.server import app, OUTPUT_DIR

client = TestClient(app)

@pytest.fixture
def mock_output_dir(tmp_path, monkeypatch):
    """Create a temporary output directory structure."""
    # Override OUTPUT_DIR in server.py
    monkeypatch.setattr("web_ui.server.OUTPUT_DIR", str(tmp_path))
    
    novel_name = "TestNovel"
    file_hash = "hash1"
    timestamp = "20240101_120000"
    
    run_path = tmp_path / novel_name / file_hash / timestamp
    run_path.mkdir(parents=True)
    
    # Create summaries.json
    summaries = [
        {
            "chapter_id": "ch1",
            "chapter_title": "Chapter 1",
            "headline": "Headline 1",
            "summary_sentences": [{"summary_text": "Detail 1"}]
        },
        {
            "chapter_id": "ch2",
            "chapter_title": "Chapter 2",
            # No headline to test compatibility
            "summary_sentences": [{"summary_text": "Detail 2"}]
        }
    ]
    
    with open(run_path / "summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f)
        
    # Create chapter content
    with open(run_path / "Chapter 1.txt", "w", encoding="utf-8") as f:
        f.write("Content of Chapter 1")
        
    return str(tmp_path), novel_name, file_hash, timestamp

def test_list_chapters_includes_headline(mock_output_dir):
    _, novel, file_hash, ts = mock_output_dir
    
    response = client.get(f"/api/novels/{novel}/{file_hash}/{ts}/chapters")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    
    # Check ch1
    ch1 = next(item for item in data if item["id"] == "ch1")
    assert ch1["headline"] == "Headline 1"
    
    # Check ch2 (compatibility)
    ch2 = next(item for item in data if item["id"] == "ch2")
    assert ch2["headline"] == ""

def test_get_chapter_detail_includes_headline(mock_output_dir):
    _, novel, file_hash, ts = mock_output_dir
    
    # Test ch1
    response = client.get(f"/api/novels/{novel}/{file_hash}/{ts}/chapters/ch1")
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == "Headline 1"
    assert data["content"] == "Content of Chapter 1"
    
    # Test ch2
    response = client.get(f"/api/novels/{novel}/{file_hash}/{ts}/chapters/ch2")
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == ""
