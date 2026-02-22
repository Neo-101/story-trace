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
        llm_client: Any = None,
        progress_callback: Callable[[int, str], None] = None
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

        # 1.5. Check if CURRENT State already exists (Cache Hit)
        # If we already have a state for target_chapter_index, we can skip analysis!
        # This is crucial for re-running the job on the same pair.
        current_state = self.store.get_state_at_chapter(
            novel_hash,
            plugin_type,
            entity_id,
            target_chapter_index,
            plugin.state_model
        )
        
        if current_state:
            # Cache Hit!
            if progress_callback:
                progress_callback(100, "Cache Hit (Skipping LLM)")
            return current_state

        # If no history, initialize blank state
        if not prev_state:
            if hasattr(plugin, 'get_initial_state'):
                prev_state = plugin.get_initial_state(entity_id)
            else:
                # Fallback or Error?
                # For now, let's assume all plugins MUST implement this or we fail gracefully
                print(f"[Engine] No previous state and no get_initial_state for {entity_id}")
                return None

        # 2. Check Trigger (Adaptive Logic)
        # Note: prev_state might be None if it's the very first chapter.
        should_trigger = False
        
        # If we have an LLM client, we check if we should trigger
        if llm_client:
            if progress_callback:
                progress_callback(10, "Checking interaction density...")
            should_trigger = plugin.check_trigger(prev_state, new_events)

        new_state = None

        if should_trigger and llm_client:
            # 3. LLM Path
            if progress_callback:
                progress_callback(30, "Generating LLM prompt...")
                
            prompt = plugin.generate_prompt(prev_state, new_events)
            
            try:
                if progress_callback:
                    progress_callback(50, "Waiting for LLM response...")
                    
                # Expecting llm_client to have a .generate(prompt) method
                response_str = llm_client.generate(prompt)
                
                if progress_callback:
                    progress_callback(80, "Parsing response...")
                
                # Parse response
                new_state = plugin.parse_response(response_str, prev_state)
                
            except Exception as e:
                print(f"[Engine] LLM Failed: {e}")
                should_trigger = False # Fallback to clone
                if progress_callback:
                    progress_callback(50, f"LLM Failed, falling back to clone. Error: {str(e)}")

        if not should_trigger or not new_state:
            # 4. Fast Path (Clone)
            # If no previous state, we can't clone. We must initialize.
            if prev_state:
                new_state = prev_state.model_copy()
                new_state.updated_at = "now"
            else:
                # First chapter, no trigger? Then no state.
                # Actually, if it's the first chapter and no interaction, we don't need a state.
                return None

        # 5. Save & Return
        if new_state:
            # Ensure correct index
            new_state.chapter_index = target_chapter_index
            self.store.save_state(novel_hash, plugin_type, entity_id, new_state)
            
            if progress_callback:
                progress_callback(100, "State saved.")
            
        return new_state
