import json
from typing import List, Type
from backend.narrative_engine.plugins.base import NarrativePlugin
from backend.narrative_engine.core.models import BaseNarrativeState, RelationshipState

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
        
    def check_trigger(self, prev_state: RelationshipState, new_events: List[dict]) -> bool:
        """
        Heuristic: Trigger if there are ANY interactions in the new block.
        Future Optimization: Check for 'strong verbs' or specific keywords.
        """
        # new_events is a list of relationship timeline events for this pair
        # If the list is empty, it means no interactions found in this block.
        if not new_events:
            return False
            
        # Basic density check: If interaction count > 0, trigger.
        return len(new_events) > 0

    def generate_prompt(self, prev_state: RelationshipState, new_events: List[dict]) -> str:
        """
        Constructs the incremental analysis prompt.
        """
        # 1. Format Events Digest
        events_text = ""
        for event in new_events:
            events_text += f"- Ch {event['chapter_id']}: {event['description']} ({event['relation']})\n"
            
        # 2. Build Prompt
        prompt = f"""
You are a literary analyst tracking the relationship between {prev_state.source} and {prev_state.target}.

### Previous State (Up to Ch {prev_state.chapter_index})
- Archetype: {prev_state.dominant_archetype}
- Stage: {prev_state.current_stage}
- Trust: {prev_state.trust_level}/100 | Romance: {prev_state.romance_level}/100 | Conflict: {prev_state.conflict_level}/100
- Summary: {prev_state.summary_so_far}
- Unresolved Threads: {json.dumps(prev_state.unresolved_threads, ensure_ascii=False)}

### New Events (Current Block)
{events_text}

### Task
Analyze how the relationship has EVOLVED based *only* on the new events.
Update the metrics and summary. If nothing significant changed, keep values stable.

### Output Format (JSON Only)
{{
    "trust_level": int,
    "romance_level": int,
    "conflict_level": int,
    "dominant_archetype": "string",
    "current_stage": "string",
    "summary_update": "string (Focus on what changed in this block)",
    "new_unresolved_threads": ["string"]
}}
"""
        return prompt

    def parse_response(self, llm_response: str, base_state: RelationshipState) -> RelationshipState:
        try:
            # Simple JSON parsing (in prod, use a robust parser/repairer)
            data = json.loads(llm_response)
            
            # Merge summary: Append new update to history
            # In a real system, we might want to summarize the summary if it gets too long.
            new_summary = base_state.summary_so_far + "\n" + data.get("summary_update", "")
            
            return RelationshipState(
                entity_id=base_state.entity_id,
                chapter_index=base_state.chapter_index, # Will be updated by engine
                summary_so_far=new_summary,
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
