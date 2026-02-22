# Design Doc v9: Entity Description History & Dynamic Context

## Problem Statement
In the current Graph View, entity descriptions are static. The backend aggregator picks the *longest* description found across all chapters and serves it as the global description. 

**Issues:**
1. **Context Mismatch**: A description like "Not appeared in this chapter" (valid for Chapter 10) becomes the permanent description for the entity even in Global Cumulative Mode, confusing the user.
2. **Loss of Evolution**: Characters evolve. A description from Chapter 1 is different from Chapter 50. The current system loses this timeline.
3. **Mode Incompatibility**: 
   - **Focus Mode**: Should show the description *specific to that chapter*.
   - **Cumulative Mode**: Should show a *comprehensive* or *latest* description up to the current timeline point.

## Proposed Solution

### 1. Backend: Description History
Instead of overwriting `description`, we will store a `history` list in `AggregatedEntity`.

**Data Structure:**
```python
class AggregatedEntity(BaseModel):
    name: str
    type: str
    description: str  # Kept for backward compatibility (smart default)
    history: List[EntityDescription]  # New field
    # ... other fields

class EntityDescription(BaseModel):
    chapter_id: str
    content: str
```

**Aggregation Logic (`core/world_builder/aggregator.py`):**
- Iterate through all chapters.
- Collect `{chapter_id, content}` for every entity appearance.
- Store in `history` sorted by chapter order.
- `description` field will still be populated with the "best" general description (e.g., longest one not containing negative keywords like "not appeared") for fallback.

### 2. Frontend: Dynamic Description Logic
The frontend `GraphView.vue` will use `timelineIndex` and `graphMode` to select the best description from `history`.

**Selection Logic:**

*   **Filter**: Get all history entries where `chapter_index <= timelineIndex`.

*   **Mode: Focus (Single Chapter)**
    *   Look for an entry where `chapter_id == currentChapterId`.
    *   If found -> Display it.
    *   If not found -> Display "No description in this chapter."

*   **Mode: Cumulative (Global)**
    *   **Strategy**: "Smart Latest"
    *   Iterate backwards from current timeline.
    *   Find the first description that does **NOT** contain negative phrases (e.g., "未出场", "未直接出现").
    *   If all are negative, fall back to the generic `description` field.
    *   **Display**: Show the selected description + Source Chapter (e.g., "Source: Chapter 5").

## Implementation Plan

1.  **Backend Models**: Update `AggregatedEntity` in `data_protocol/models.py` (if needed) or just ensure `aggregator.py` outputs the dict correctly if using loose schemas. *Correction: `AggregatedEntity` is a Pydantic model, so it must be updated.*
2.  **Backend Aggregator**: Modify `EntityAggregator.aggregate_entities` to populate `history`.
3.  **Frontend Types**: Update `Entity` interface in `web_ui_v2/src/types/index.ts`.
4.  **Frontend Component**: Update `GraphView.vue` to implement the selection logic and update the UI panel.
