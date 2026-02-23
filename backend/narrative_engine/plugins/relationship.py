import json
from typing import List, Type
from backend.narrative_engine.plugins.base import NarrativePlugin
from backend.narrative_engine.core.models import BaseNarrativeState, RelationshipState, AnalysisEvent
from backend.narrative_engine.prompts import RELATIONSHIP_ANALYSIS_TEMPLATE

class RelationshipPlugin(NarrativePlugin):
    """
    Pilot Plugin: Tracks character relationship dynamics.
    """
    
    @property
    def plugin_type(self) -> str:
        return "relationship"
        
    @property
    def state_model(self) -> Type[BaseNarrativeState]:
        return RelationshipState
        
    def get_initial_state(self, entity_id: str, **kwargs) -> RelationshipState:
        source, target = entity_id.split("_")
        return RelationshipState(
            entity_id=entity_id,
            chapter_index=0,
            summary_so_far="Initial state. No interactions yet.",
            source=source,
            target=target,
            trust_level=50, # Neutral
            romance_level=0,
            conflict_level=0,
            dominant_archetype="Stranger",
            current_stage="Introduction"
        )
        
    def check_trigger(self, prev_state: RelationshipState, new_events: List[AnalysisEvent]) -> bool:
        """
        Heuristic: Trigger if there are ANY interactions in the new block.
        Future Optimization: Check for 'strong verbs' or specific keywords.
        """
        # new_events is a list of AnalysisEvent objects
        if not new_events:
            return False
            
        # Basic density check: If interaction count > 0, trigger.
        return len(new_events) > 0

    def generate_prompt(self, prev_state: RelationshipState, new_events: List[AnalysisEvent]) -> str:
        """
        Constructs the incremental analysis prompt.
        """
        # 1. Format Events Digest
        events_text = ""
        for event in new_events:
            # Handle AnalysisEvent object
            idx = event.chapter_index
            content = event.content
            
            desc = "\n  ".join(content)
            events_text += f"- Ch {idx}:\n  {desc}\n"
            
        # 2. Build Prompt using Template
        prompt = RELATIONSHIP_ANALYSIS_TEMPLATE.format(
            source=prev_state.source,
            target=prev_state.target,
            prev_chapter_index=prev_state.chapter_index,
            dominant_archetype=prev_state.dominant_archetype,
            current_stage=prev_state.current_stage,
            trust_level=prev_state.trust_level,
            romance_level=prev_state.romance_level,
            conflict_level=prev_state.conflict_level,
            summary_so_far=prev_state.summary_so_far,
            unresolved_threads=json.dumps(prev_state.unresolved_threads, ensure_ascii=False),
            events_text=events_text
        )
        return prompt

    def parse_response(self, llm_response: str, base_state: RelationshipState) -> RelationshipState:
        try:
            # Simple JSON parsing (in prod, use a robust parser/repairer)
            data = json.loads(llm_response)
            
            # Revised summary replaces the old one
            # If revised_summary is missing (legacy LLM output), fallback to append logic
            revised_summary = data.get("revised_summary")
            if not revised_summary:
                 revised_summary = base_state.summary_so_far + "\n" + data.get("summary_update", "")
            
            return RelationshipState(
                entity_id=base_state.entity_id,
                chapter_index=base_state.chapter_index, # Will be updated by engine
                summary_so_far=revised_summary,
                source=base_state.source,
                target=base_state.target,
                trust_level=data.get("trust_level", base_state.trust_level),
                romance_level=data.get("romance_level", base_state.romance_level),
                conflict_level=data.get("conflict_level", base_state.conflict_level),
                dominant_archetype=data.get("dominant_archetype", base_state.dominant_archetype),
                current_stage=data.get("current_stage", base_state.current_stage),
                unresolved_threads=data.get("new_unresolved_threads", base_state.unresolved_threads)
            )
        except Exception as e:
            print(f"[RelationshipPlugin] Parse Error: {e}")
            # Fallback: Return previous state
            return base_state
