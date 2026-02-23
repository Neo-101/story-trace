import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.server import app
from backend.routers.analysis import get_session
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity

# Use in-memory SQLite for testing
# check_same_thread=False is needed because FastAPI runs in a different thread context? 
# Actually TestClient runs in the same thread usually, but good practice for SQLite.
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        TEST_DB_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_db_data(session: Session):
    """Create initial DB data for testing"""
    # 1. Novel & Version & Run
    novel = Novel(name="EntityNovel")
    session.add(novel)
    session.commit()
    
    version = NovelVersion(novel_id=novel.id, hash="hash_ent")
    session.add(version)
    session.commit()
    
    run = AnalysisRun(version_id=version.id, timestamp="20240101_100000")
    session.add(run)
    session.commit()
    
    # 2. Chapter 1 (With Entities)
    ch1 = Chapter(
        run_id=run.id, 
        chapter_index=1, 
        title="Chapter 1", 
        headline="Headline 1",
        content="Content of Chapter 1"
    )
    session.add(ch1)
    session.commit()
    
    # Add summaries for Ch1
    s1 = Summary(chapter_id=ch1.id, text="Detail 1")
    session.add(s1)
    
    # Add entities for Ch1
    e1 = Entity(chapter_id=ch1.id, name="Alice", type="Person", description="Protagonist", confidence=0.9)
    e2 = Entity(chapter_id=ch1.id, name="Wonderland", type="Location", description="Setting", confidence=0.8)
    session.add(e1)
    session.add(e2)
    session.commit()
    
    # 3. Chapter 2 (No Entities)
    ch2 = Chapter(
        run_id=run.id, 
        chapter_index=2, 
        title="Chapter 2", 
        content="Content of Chapter 2"
    )
    session.add(ch2)
    session.commit()
    
    # Add summaries for Ch2
    s2 = Summary(chapter_id=ch2.id, text="Detail 2")
    session.add(s2)
    session.commit()

    return novel.name, version.hash, run.timestamp, ch1.id, ch2.id

def test_get_chapter_detail_returns_entities(client, mock_db_data):
    novel_name, file_hash, ts, ch1_id, ch2_id = mock_db_data
    
    # Test ch1 (has entities)
    response = client.get(f"/api/novels/{novel_name}/{file_hash}/{ts}/chapters/{ch1_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert "entities" in data
    assert len(data["entities"]) == 2
    
    # Verify Entity 1
    ent1 = next(e for e in data["entities"] if e["name"] == "Alice")
    assert ent1["type"] == "Person"
    assert ent1["description"] == "Protagonist"
    assert ent1["confidence"] == 0.9
    
    # Test ch2 (no entities)
    response = client.get(f"/api/novels/{novel_name}/{file_hash}/{ts}/chapters/{ch2_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert "entities" in data
    assert data["entities"] == []
