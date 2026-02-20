import json
import pytest
from fastapi.testclient import TestClient
from web_ui.server import app, OUTPUT_DIR

client = TestClient(app)

@pytest.fixture
def mock_output_dir_with_entities(tmp_path, monkeypatch):
    """Create a temporary output directory structure with entity data."""
    # Override OUTPUT_DIR in server.py
    monkeypatch.setattr("web_ui.server.OUTPUT_DIR", str(tmp_path))
    
    novel_name = "EntityNovel"
    file_hash = "hash_ent"
    timestamp = "20240101_100000"
    
    run_path = tmp_path / novel_name / file_hash / timestamp
    run_path.mkdir(parents=True)
    
    # Create summaries.json with entities
    summaries = [
        {
            "chapter_id": "ch1",
            "chapter_title": "Chapter 1",
            "headline": "Headline 1",
            "summary_sentences": [{"summary_text": "Detail 1"}],
            "entities": [
                {"name": "Alice", "type": "Person", "description": "Protagonist"},
                {"name": "Wonderland", "type": "Location", "description": "Setting"}
            ]
        },
        {
            "chapter_id": "ch2",
            "chapter_title": "Chapter 2",
            "summary_sentences": [{"summary_text": "Detail 2"}],
            # No entities field (backward compatibility)
        }
    ]
    
    with open(run_path / "summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f)
        
    # Create chapter content
    with open(run_path / "Chapter 1.txt", "w", encoding="utf-8") as f:
        f.write("Content of Chapter 1")
        
    return str(tmp_path), novel_name, file_hash, timestamp

def test_get_chapter_detail_returns_entities(mock_output_dir_with_entities):
    _, novel, file_hash, ts = mock_output_dir_with_entities
    
    # Test ch1 (has entities)
    response = client.get(f"/api/novels/{novel}/{file_hash}/{ts}/chapters/ch1")
    assert response.status_code == 200
    data = response.json()
    
    assert "entities" in data
    assert len(data["entities"]) == 2
    assert data["entities"][0]["name"] == "Alice"
    assert data["entities"][0]["type"] == "Person"
    
    # Test ch2 (no entities)
    response = client.get(f"/api/novels/{novel}/{file_hash}/{ts}/chapters/ch2")
    assert response.status_code == 200
    data = response.json()
    
    assert "entities" in data
    assert data["entities"] == []
