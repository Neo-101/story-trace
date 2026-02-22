import shutil
import unittest
import json
from pathlib import Path
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.engine import NarrativeEvolutionEngine
from backend.narrative_engine.plugins.relationship import RelationshipPlugin
from backend.narrative_engine.core.models import RelationshipState

class MockLLMClient:
    """Mock LLM for testing integration"""
    def generate(self, prompt: str) -> str:
        # Simulate a smart response
        return json.dumps({
            "trust_level": 10,
            "romance_level": 0,
            "conflict_level": 90,
            "dominant_archetype": "Rival",
            "current_stage": "Conflict Escalation",
            "summary_update": "A fierce battle broke out.",
            "new_unresolved_threads": ["Who stole the artifact?"]
        })

class TestEngineIntegration(unittest.TestCase):
    TEST_CACHE_DIR = "tests/temp_engine_cache"

    def setUp(self):
        self.store = StateStore(base_path=self.TEST_CACHE_DIR)
        self.engine = NarrativeEvolutionEngine(self.store)
        self.plugin = RelationshipPlugin()
        self.engine.register_plugin(self.plugin)
        self.mock_llm = MockLLMClient()

    def tearDown(self):
        if Path(self.TEST_CACHE_DIR).exists():
            shutil.rmtree(self.TEST_CACHE_DIR)

    def test_evolve_workflow(self):
        """Test the full lifecycle: Init -> Trigger -> Evolve -> Save"""
        entity_id = "Hero_Villain"
        novel_hash = "test_novel_123"
        
        # 1. Step 1: Chapter 1 (Initial Interaction)
        events_ch1 = [
            {"chapter_id": "1", "description": "Hero meets Villain.", "relation": "Meeting"}
        ]
        
        state_ch1 = self.engine.evolve_state(
            novel_hash=novel_hash,
            plugin_type="relationship",
            entity_id=entity_id,
            target_chapter_index=1,
            new_events=events_ch1,
            llm_client=self.mock_llm
        )
        
        # Verification 1: State should be updated (Mock LLM values)
        self.assertEqual(state_ch1.trust_level, 10)
        self.assertEqual(state_ch1.dominant_archetype, "Rival")
        self.assertIn("A fierce battle broke out.", state_ch1.summary_so_far)
        
        # 2. Step 2: Chapter 2 (No Events)
        # Should NOT trigger LLM (Fast Path)
        state_ch2 = self.engine.evolve_state(
            novel_hash=novel_hash,
            plugin_type="relationship",
            entity_id=entity_id,
            target_chapter_index=2,
            new_events=[], # Empty
            llm_client=self.mock_llm
        )
        
        # Verification 2: State should be cloned (same as Ch1 but new index)
        self.assertEqual(state_ch2.chapter_index, 2)
        self.assertEqual(state_ch2.trust_level, 10) # Carried over
        self.assertEqual(state_ch2.summary_so_far, state_ch1.summary_so_far)
        
        # 3. Check Persistence
        loaded = self.store.get_latest_state(
            novel_hash, "relationship", entity_id, 
            before_chapter=3, 
            model_class=RelationshipState
        )
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.chapter_index, 2)
        self.assertEqual(loaded.trust_level, 10)

if __name__ == '__main__':
    unittest.main()
