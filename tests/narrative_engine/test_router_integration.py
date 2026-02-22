import unittest
from unittest.mock import MagicMock, patch
from backend.narrative_engine.core.models import RelationshipState
from backend.routers.analysis import get_relationship_timeline

class MockChapter:
    def __init__(self, id, chapter_index, title):
        self.id = id
        self.chapter_index = chapter_index
        self.title = title
        self.summaries = []
        self.entities = []
        self.relationships = []
        self.headline = "Headline"
        self.content = "Content"

class MockSummary:
    def __init__(self, text):
        self.summary_text = text
        self.source_spans = []

class MockRelationship:
    def __init__(self, source, target, relation, description):
        self.source = source
        self.target = target
        self.relation = relation
        self.description = description
        self.confidence = 1.0

class TestRouterIntegration(unittest.TestCase):
    
    @patch("backend.routers.analysis.get_merged_chapters")
    @patch("backend.routers.analysis._state_store")
    def test_get_relationship_timeline_with_state(self, mock_store, mock_get_chapters):
        # 1. Setup Mock Data
        # A chapter with an interaction
        chapter = MockChapter(id=1, chapter_index=10, title="The Conflict")
        # Add a dummy relationship to the chapter (via db_chapter_to_summary logic mocking)
        # Wait, get_relationship_timeline calls db_chapter_to_summary which reads attributes.
        # We need to structure MockChapter to satisfy db_chapter_to_summary
        
        # We need to mock the Summary object structure inside the chapter
        # In `db_chapter_to_summary`:
        # for s in db_chapter.summaries: ...
        # for r in db_chapter.relationships: ...
        
        rel = MockRelationship("Hero", "Villain", "Attack", "Hero attacks Villain")
        chapter.relationships = [rel]
        
        mock_get_chapters.return_value = [chapter]
        
        # 2. Setup Mock State Store
        # Should return a state for chapter 10
        state = RelationshipState(
            entity_id="Hero_Villain",
            chapter_index=10,
            summary_so_far="They are fighting.",
            source="Hero",
            target="Villain",
            trust_level=5,
            dominant_archetype="Enemy"
        )
        mock_store.list_history.return_value = [state]
        
        # 3. Call the function (No DB session needed as we mocked get_merged_chapters)
        result = get_relationship_timeline(
            novel_name="test",
            file_hash="hash",
            timestamp="123",
            source="Hero",
            target="Villain",
            session=MagicMock()
        )
        
        # 4. Verify
        self.assertEqual(len(result), 1)
        event = result[0]
        self.assertEqual(event.chapter_id, "1")
        
        # CHECK: narrative_state should be present
        self.assertIsNotNone(event.narrative_state)
        self.assertEqual(event.narrative_state["trust_level"], 5)
        self.assertEqual(event.narrative_state["dominant_archetype"], "Enemy")
        
        print("Successfully verified API response contains narrative_state!")

if __name__ == '__main__':
    unittest.main()
