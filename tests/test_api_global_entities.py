import os
import json
import pytest
from fastapi.testclient import TestClient
from web_ui.server import app, OUTPUT_DIR
from data_protocol.models import ChapterSummary, Entity, SummarySentence, TextSpan

client = TestClient(app)

@pytest.fixture
def mock_novel_data(tmp_path):
    # Mock output directory structure
    novel_name = "TestNovel"
    file_hash = "hash123"
    timestamp = "20240101_120000"
    
    run_path = tmp_path / novel_name / file_hash / timestamp
    run_path.mkdir(parents=True)
    
    # Create summaries.json
    summaries = [
        ChapterSummary(
            chapter_id="ch1",
            chapter_title="Chapter 1",
            headline="Start",
            summary_sentences=[],
            entities=[
                Entity(name="Hero", type="Person", description="Main character", confidence=1.0)
            ]
        ).model_dump(),
        ChapterSummary(
            chapter_id="ch2",
            chapter_title="Chapter 2",
            headline="Middle",
            summary_sentences=[],
            entities=[
                Entity(name="Hero", type="Person", description="Still main character", confidence=1.0),
                Entity(name="Villain", type="Person", description="Bad guy", confidence=0.9)
            ]
        ).model_dump()
    ]
    
    with open(run_path / "summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False)
        
    return str(tmp_path), novel_name, file_hash, timestamp

def test_get_global_entities(mock_novel_data, monkeypatch):
    root_dir, novel_name, file_hash, timestamp = mock_novel_data
    
    # Mock OUTPUT_DIR in server.py
    monkeypatch.setattr("web_ui.server.OUTPUT_DIR", root_dir)
    
    response = client.get(f"/api/novels/{novel_name}/{file_hash}/{timestamp}/entities")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Check Hero
    hero = next(e for e in data if e["name"] == "Hero")
    assert hero["count"] == 2
    assert set(hero["chapter_ids"]) == {"ch1", "ch2"}
    
    # Check Villain
    villain = next(e for e in data if e["name"] == "Villain")
    assert villain["count"] == 1
    assert villain["chapter_ids"] == ["ch2"]

def test_get_global_entities_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr("web_ui.server.OUTPUT_DIR", str(tmp_path))
    response = client.get("/api/novels/Unknown/hash/time/entities")
    assert response.status_code == 404
