import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, SQLModel, create_engine, select
from backend.narrative_engine.plugins.concept import ConceptAnalyzer
from backend.schemas import TimelineEvent
from data_protocol.models import ConceptStage
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Entity

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
    
    # Create Chapters and Entities
    # Ch1: Rumor
    ch1 = Chapter(run_id=run.id, chapter_index=1, title="Intro", content="Some rumor content.")
    entity1 = Entity(name="MysteryBox", type="Object", description="A mysterious box.", confidence=1.0)
    ch1.entities.append(entity1)
    session.add(ch1)
    
    # Ch2: Fact
    ch2 = Chapter(run_id=run.id, chapter_index=2, title="Discovery", content="It is made of wood.")
    entity2 = Entity(name="MysteryBox", type="Object", description="Wooden box.", confidence=1.0)
    ch2.entities.append(entity2)
    session.add(ch2)
    
    session.commit()
    return {"novel": novel, "version": version, "run": run}

def test_concept_analysis_flow(session, mock_data):
    # 1. Mock Context Manager to return a fake timeline
    # We can mock the get_entity_chronicle method
    with patch("backend.narrative_engine.plugins.concept.ContextManager") as MockContextManager:
        mock_ctx = MockContextManager.return_value
        mock_ctx.get_entity_chronicle.return_value = [
            TimelineEvent(chapter_id="1", chapter_index=1, chapter_title="Intro", content=["Rumors say it's cursed."], gap_before=0),
            TimelineEvent(chapter_id="2", chapter_index=2, chapter_title="Discovery", content=["It's just a wooden box."], gap_before=0)
        ]
        mock_ctx.format_chronicle_for_prompt.return_value = "Formatted Timeline"

        # 2. Mock LLM Client
        mock_llm = MagicMock()
        # Mock response mimicking the JSON output
        mock_llm.generate.return_value = """
        ```json
        [
            {
                "chapter_index": 1,
                "stage_name": "Rumor",
                "description": "传说中的诅咒之盒",
                "revealed_by": ["Rumors say it's cursed"]
            },
            {
                "chapter_index": 2,
                "stage_name": "Fact",
                "description": "普通的木盒子",
                "revealed_by": ["It's just a wooden box"]
            }
        ]
        ```
        """

        # 3. Run Analyzer
        analyzer = ConceptAnalyzer(session, mock_llm)
        stages = analyzer.analyze_entity("TestNovel", "hash123", "MysteryBox")

        # 4. Verify Results
        assert len(stages) == 2
        assert stages[0].stage_name == "Rumor"
        assert stages[1].stage_name == "Fact"
        
        # 5. Verify DB Updates
        # Re-fetch entities from DB
        
        # Ch1
        statement = select(Entity).join(Chapter).where(Chapter.chapter_index == 1, Entity.name == "MysteryBox")
        e1 = session.exec(statement).first()
        assert e1 is not None
        assert "Rumor" in e1.concept_evolution_json
        
        # Ch2
        statement = select(Entity).join(Chapter).where(Chapter.chapter_index == 2, Entity.name == "MysteryBox")
        e2 = session.exec(statement).first()
        assert e2 is not None
        assert "Fact" in e2.concept_evolution_json

if __name__ == "__main__":
    # Manually run if executed directly
    pass
