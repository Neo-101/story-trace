from typing import List, Dict, Type, Any
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.models import BaseNarrativeState
from backend.narrative_engine.plugins.base import NarrativePlugin

class NarrativeEvolutionEngine:
    """
    Orchestrates the incremental analysis of narrative entities.
    """
    def __init__(self, store: StateStore):
        self.store = store
        self.plugins: Dict[str, NarrativePlugin] = {}

    def register_plugin(self, plugin: NarrativePlugin):
        """Register a plugin (e.g., 'relationship')"""
        self.plugins[plugin.plugin_type] = plugin

    def evolve_state(
        self,
        novel_hash: str,
        plugin_type: str,
        entity_id: str,
        target_chapter_index: int,
        new_events: List[Dict[str, Any]],
        llm_client: Any = None # Optional for now, will be used later
    ) -> BaseNarrativeState:
        """
        Main Loop:
        1. Load previous state (Snapshot N).
        2. Check if we need to run LLM (Adaptive Trigger).
        3. If yes, generate prompt -> call LLM -> parse -> save new state (Snapshot N+1).
        4. If no, clone previous state -> save new state (Snapshot N+1).
        """
        plugin = self.plugins.get(plugin_type)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_type}' not registered.")

        # 1. Load Previous State
        # We look for the latest checkpoint BEFORE the target chapter
        prev_state = self.store.get_latest_state(
            novel_hash, 
            plugin_type, 
            entity_id, 
            before_chapter=target_chapter_index,
            model_class=plugin.state_model
        )

        # If no history, initialize blank state
        if not prev_state:
            prev_state = plugin.get_initial_state(entity_id)
            # If initial state, we might assume chapter_index=0
            # But the new state will be at target_chapter_index

        # 2. Check Trigger (Adaptive Logic)
        should_trigger = plugin.check_trigger(prev_state, new_events)

        new_state = None

        if should_trigger and llm_client:
            # 3. LLM Path
            prompt = plugin.generate_prompt(prev_state, new_events)
            
            try:
                # Expecting llm_client to have a .generate(prompt) method
                response_str = llm_client.generate(prompt)
                
                # Parse response
                new_state = plugin.parse_response(response_str, prev_state)
                
            except Exception as e:
                print(f"[Engine] LLM Failed: {e}")
                should_trigger = False # Fallback to clone

        if not should_trigger or not new_state:
            # 4. Fast Path (Clone)
            # We simply extend the previous state to the new timestamp.
            # We must create a NEW instance, not mutate the old one.
            new_state = prev_state.model_copy()
            new_state.chapter_index = target_chapter_index
            new_state.updated_at = "now" # In real code, use datetime
            # Note: We might want to append "No significant events" to summary?
            # For now, keep it clean.

        # 5. Save & Return
        if new_state:
            # Ensure correct index
            new_state.chapter_index = target_chapter_index
            self.store.save_state(novel_hash, plugin_type, new_state)
            
        return new_state
