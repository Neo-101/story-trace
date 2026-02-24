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

CONCEPT_EVOLUTION_TEMPLATE = """
You are a literary analyst specializing in world-building and plot twists.
Your task is to analyze the evolution of the concept '{entity_name}' based on its chronicle.

### Entity Chronicle (Time-ordered events)
{chronicle_text}

### Analysis Guidelines
Identify distinct stages of understanding about '{entity_name}':
- **Rumor (传闻)**: Unverified information, myths, hearsay, or initial impressions that might be misleading.
- **Fact (事实)**: Concrete details confirmed by reliable sources, direct observation, or general consensus.
- **Truth (真相/核心)**: The deep underlying reality, often revealing a plot twist, subverting previous facts, or exposing the true nature of the concept.

Not every concept goes through all stages. Some might start as Fact and stay Fact. Others might go Rumor -> Truth.
Focus on *significant shifts* in understanding.

### Output Requirements
Return a JSON list of stages. For each stage, identify:
1. `chapter_index`: The chapter index where this stage was FIRST revealed or became dominant.
2. `stage_name`: One of "Rumor", "Fact", "Truth".
3. `description`: A concise description of the concept at this stage (in Chinese).
4. `revealed_by`: A list of key clues, events, or dialogues that revealed this stage (in Chinese).

**IMPORTANT: Output MUST be in Chinese (Simplified).**

### Output Format (JSON Only)
[
  {{
    "chapter_index": int,
    "stage_name": "Rumor/Fact/Truth",
    "description": "string (Chinese)",
    "revealed_by": ["string (Chinese)"]
  }}
]
"""
