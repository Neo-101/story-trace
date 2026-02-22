import shutil
import unittest
from pathlib import Path
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.models import RelationshipState

class TestStateStore(unittest.TestCase):
    TEST_CACHE_DIR = "tests/temp_cache"
    
    def setUp(self):
        # Create a fresh store for each test
        self.store = StateStore(base_path=self.TEST_CACHE_DIR)
        
    def tearDown(self):
        # Cleanup
        if Path(self.TEST_CACHE_DIR).exists():
            shutil.rmtree(self.TEST_CACHE_DIR)

    def test_save_and_load_relationship_state(self):
        # 1. Create a dummy state
        state = RelationshipState(
            entity_id="LiXiaoyao_LinYueru",
            chapter_index=10,
            summary_so_far="Initial meeting.",
            source="LiXiaoyao",
            target="LinYueru",
            trust_level=20,
            romance_level=5,
            conflict_level=80,
            dominant_archetype="Rival",
            current_stage="First Fight"
        )
        
        # 2. Save it
        self.store.save_state("test_novel", "relationship", state)
        
        # 3. Verify file exists
        expected_path = Path(self.TEST_CACHE_DIR) / "test_novel" / "relationship" / "LiXiaoyao_LinYueru" / "checkpoint_10.json"
        self.assertTrue(expected_path.exists())
        
        # 4. Load it back using exact index (not typical usage but for verification)
        # Note: get_latest_state searches BEFORE the given chapter.
        # So to find ch10, we must ask for before=11
        loaded_state = self.store.get_latest_state(
            "test_novel", "relationship", "LiXiaoyao_LinYueru", 
            before_chapter=11, 
            model_class=RelationshipState
        )
        
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.chapter_index, 10)
        self.assertEqual(loaded_state.trust_level, 20)
        self.assertEqual(loaded_state.source, "LiXiaoyao")

    def test_incremental_retrieval(self):
        """Test getting the *latest* state from a sequence"""
        entity_id = "A_B"
        
        # Save checkpoints at ch 5, 10, 15
        for idx in [5, 10, 15]:
            s = RelationshipState(
                entity_id=entity_id,
                chapter_index=idx,
                summary_so_far=f"Summary at {idx}",
                source="A", target="B",
                trust_level=min(idx * 5, 100) # Ensure <= 100
            )
            self.store.save_state("test_novel", "relationship", s)
            
        # Case 1: Query for ch 12 -> Should get ch 10
        state_12 = self.store.get_latest_state("test_novel", "relationship", entity_id, before_chapter=12, model_class=RelationshipState)
        self.assertIsNotNone(state_12)
        self.assertEqual(state_12.chapter_index, 10)
        
        # Case 2: Query for ch 20 -> Should get ch 15
        state_20 = self.store.get_latest_state("test_novel", "relationship", entity_id, before_chapter=20, model_class=RelationshipState)
        self.assertEqual(state_20.chapter_index, 15)
        
        # Case 3: Query for ch 5 -> Should get None (no checkpoint before 5)
        state_5 = self.store.get_latest_state("test_novel", "relationship", entity_id, before_chapter=5, model_class=RelationshipState)
        self.assertIsNone(state_5)

if __name__ == '__main__':
    unittest.main()
