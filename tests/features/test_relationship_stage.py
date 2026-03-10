import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, SQLModel, create_engine, select
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, StoryRelationship, RelationshipStage
from backend.schemas import RelationshipStageRequest

# Mock DB Setup
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def mock_data(session):
    # Create Novel, Version, Run
    novel = Novel(name="TestNovel")
    session.add(novel)
    session.commit()
    
    version = NovelVersion(novel_id=novel.id, hash="hash123", filename="test.txt")
    session.add(version)
    session.commit()
    
    run = AnalysisRun(version_id=version.id, timestamp="20230101", status="completed")
    session.add(run)
    session.commit()
    
    # Create Chapters with Relationships
    # Ch1: A -> B (Friend)
    ch1 = Chapter(run_id=run.id, chapter_index=1, title="Meeting", content="A met B.")
    session.add(ch1)
    session.commit() # Get ID
    
    sum1 = Summary(chapter_id=ch1.id, text="A meets B.")
    session.add(sum1)
    
    rel1 = StoryRelationship(chapter_id=ch1.id, source="Alice", target="Bob", relation="Friend", description="They shook hands.", confidence=0.8)
    session.add(rel1)
    
    # Ch2: B -> A (Enemy)
    ch2 = Chapter(run_id=run.id, chapter_index=2, title="Betrayal", content="B betrayed A.")
    session.add(ch2)
    session.commit()
    
    sum2 = Summary(chapter_id=ch2.id, text="B stabs A.")
    session.add(sum2)
    
    rel2 = StoryRelationship(chapter_id=ch2.id, source="Bob", target="Alice", relation="Enemy", description="B stabbed A.", confidence=0.9)
    session.add(rel2)
    
    session.commit()
    return {"novel": novel, "version": version, "run": run}

def test_relationship_stage_analysis(session, mock_data):
    # Import the function to test
    # Note: We need to import inside test to avoid early import issues if environment not set, 
    # but here we are in same process.
    from backend.routers.analysis import analyze_relationship_stage
    
    # Mock dependencies
    with patch("backend.routers.analysis.ClientFactory") as MockClientFactory:
        # Mock LLM Client
        mock_llm = MagicMock()
        mock_llm.generate.return_value = """
        {
            "stage_label": "Betrayal",
            "summary_text": "Alice and Bob started as friends but Bob betrayed Alice.",
            "sentiment_score": -0.8
        }
        """
        MockClientFactory.create_client.return_value = mock_llm
        
        # Prepare Request
        request = RelationshipStageRequest(
            source_entity="Alice",
            target_entity="Bob",
            chapter_start=1,
            chapter_end=2,
            force=True
        )
        
        # Run Analysis
        response = analyze_relationship_stage("TestNovel", "hash123", request, session)
        
        # Verify Response
        assert response.stage_label == "Betrayal"
        assert response.sentiment_score == -0.8
        assert response.is_cached == False
        
        # Verify DB Persistence
        statement = select(RelationshipStage).where(
            RelationshipStage.novel_name == "TestNovel",
            RelationshipStage.source_entity == "Alice",
            RelationshipStage.target_entity == "Bob"
        )
        stage = session.exec(statement).first()
        assert stage is not None
        assert stage.stage_label == "Betrayal"
        assert stage.event_count == 2 # 2 interactions
        
        # Test Cache Hit (force=False)
        request.force = False
        response_cached = analyze_relationship_stage("TestNovel", "hash123", request, session)
        assert response_cached.is_cached == True
        # Ensure LLM not called again
        assert mock_llm.generate.call_count == 1

if __name__ == "__main__":
    # Manually run if executed directly
    # Need to setup session manually
    pass
