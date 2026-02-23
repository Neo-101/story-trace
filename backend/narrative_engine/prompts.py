from typing import List
import json

RELATIONSHIP_ANALYSIS_TEMPLATE = """
You are a literary analyst tracking the relationship between {source} and {target}.

### Previous State (Up to Ch {prev_chapter_index})
- Archetype: {dominant_archetype}
- Stage: {current_stage}
- Trust: {trust_level}/100 | Romance: {romance_level}/100 | Conflict: {conflict_level}/100
- Summary: {summary_so_far}
- Unresolved Threads: {unresolved_threads}

### New Events (Current Block)
{events_text}

### Task
Analyze how the relationship has EVOLVED based on the new events.
1. Update the metrics (Trust/Romance/Conflict).
2. **REWRITE** the `summary_so_far` to incorporate the new events.
   - The new summary should be a holistic description of the relationship status.
   - Keep it concise (under 300 words).
   - Retain important history while integrating new developments.

**IMPORTANT: Output MUST be in Chinese (Simplified).**
- `dominant_archetype` and `current_stage` should be concise Chinese terms (e.g., "盟友", "信任危机").
- `revised_summary` should be the updated narrative summary (replacing the old one).

### Output Format (JSON Only)
{{
    "trust_level": int,
    "romance_level": int,
    "conflict_level": int,
    "dominant_archetype": "string (Chinese)",
    "current_stage": "string (Chinese)",
    "revised_summary": "string (Chinese)",
    "new_unresolved_threads": ["string (Chinese)"]
}}
"""
