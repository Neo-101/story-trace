
import sys
import os
import json
from typing import List, Dict, Any

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.narrative_engine.core.engine import NarrativeEvolutionEngine
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.plugins.relationship import RelationshipPlugin
from backend.narrative_engine.core.models import RelationshipState

# Mock LLM Client
class MockLLMClient:
    def generate(self, prompt: str) -> str:
        print("\n[MockLLM] Generating response for prompt:")
        print("-" * 20)
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        print("-" * 20)
        return json.dumps({
            "trust_level": 60,
            "romance_level": 10,
            "conflict_level": 5,
            "dominant_archetype": "盟友",
            "current_stage": "初步合作",
            "summary_update": "两人通过合作建立了初步信任。",
            "new_unresolved_threads": []
        })

def debug_evolution():
    print("DEBUG: Starting relationship evolution debug...")
    
    # 1. Setup
    store = StateStore()
    engine = NarrativeEvolutionEngine(store)
    plugin = RelationshipPlugin()
    engine.register_plugin(plugin)
    
    # 2. Mock Data (Simulating jobs.py output)
    novel_hash = "8771c958"
    pair_id = "孙杰克_塔派"
    chapter_index = 3 # Chapter 3 has interactions
    
    # This matches the structure in jobs.py
    new_events = [{
        "chapter_index": chapter_index,
        "content": [
            "Interaction (询问): 孙杰克向机器人询问逃生飞船位置。",
            "Interaction (带领): 孙杰克带领机器人返回观光舱。"
        ]
    }]
    
    print(f"DEBUG: Mock events prepared for Ch {chapter_index}")
    
    # 3. Run Evolution
    try:
        print("DEBUG: Calling evolve_state...")
        state = engine.evolve_state(
            novel_hash=novel_hash,
            plugin_type="relationship",
            entity_id=pair_id,
            target_chapter_index=chapter_index,
            new_events=new_events,
            llm_client=MockLLMClient(),
            progress_callback=lambda p, m: print(f"[Progress {p}%] {m}")
        )
        
        if state:
            print("\nDEBUG: Success! State generated:")
            print(state.model_dump_json(indent=2))
        else:
            print("\nDEBUG: Failed! No state returned.")
            
    except Exception as e:
        print("\nDEBUG: Exception caught during evolution!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_evolution()
