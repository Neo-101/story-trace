# Technical Specification: Unified Narrative Evolution Engine (v1.0)

**Project Code**: `NARRATIVE_STATE_MACHINE`
**Feature**: Dynamic Relationship Arc (Pilot Module)
**Status**: Draft
**Owner**: StoryTrace Architecture Team

---

## 1. Executive Summary
This document defines the architecture for the **Unified Narrative Evolution Engine**, a system designed to track the chronological evolution of narrative entities (Characters, Locations, Items, Factions) through a state-machine approach. 
The pilot implementation will focus on **Character Relationships**, solving the problem of high-cost, repetitive analysis via an **Incremental State Caching** and **Adaptive Triggering** strategy.

---

## 2. Core Architecture

### 2.1 The "Block-Based" Narrative Model
We treat the novel as a sequence of immutable **Analysis Blocks**.
- **Block**: A logical unit of narrative time (e.g., 1 Chapter, or a batch of 5 Chapters).
- **State**: The snapshot of an entity's status at the end of a Block.
- **Transition**: The function `f(State_N, Events_N+1) -> State_N+1`.

### 2.2 System Components
1.  **`NarrativeEvolutionEngine` (Core)**:
    - Orchestrates the loading, calculation, and saving of states.
    - Manages the "Zipper" logic (merging cached states with new analysis).
    - Implements the **Adaptive Triggering** strategy to minimize LLM calls.

2.  **`StateStore` (Persistence)**:
    - A file-based or database-backed storage for State Snapshots.
    - Path Convention: `cache/narrative/{novel_hash}/{plugin_type}/{entity_id}/checkpoint_{chapter_idx}.json`

3.  **`Plugins` (Business Logic)**:
    - **`RelationshipPlugin` (Pilot)**: Tracks `(A, B)` dynamics.
    - *Future*: `WorldPlugin`, `ItemPlugin`, `FactionPlugin`.

---

## 3. Data Schema (Pydantic Models)

### 3.1 Base State (Abstract)
```python
class BaseNarrativeState(BaseModel):
    chapter_index: int       # The point in time this state represents
    summary_so_far: str      # LLM-generated summary of the entity's history up to this point
    key_tags: List[str]      # High-level tags (e.g., "Rival", "Cursed")
    updated_at: str          # Timestamp
```

### 3.2 Relationship State (Concrete)
```python
class RelationshipState(BaseNarrativeState):
    source: str              # Entity A
    target: str              # Entity B
    
    # Quantitative Metrics (0-100)
    trust_level: int
    romance_level: int
    conflict_level: int
    
    # Qualitative Analysis
    dominant_archetype: str  # e.g., "Enemies to Lovers", "Mentor/Student"
    current_stage: str       # e.g., "The Misunderstanding", "The Betrayal"
    
    # Memory
    unresolved_threads: List[str] # Issues carried over to next block
```

---

## 4. Workflow: The "Adaptive Triggering" Loop

**Scenario**: Analyzing Relationship (A, B) for Chapters 21-30.

1.  **Load Context**:
    - Engine requests `StateStore.get_latest_checkpoint(A, B, before=21)`.
    - Returns: `State(Ch20)`.

2.  **Pre-Flight Check (Local)**:
    - Engine scans `ChapterSummary` for Ch 21-30.
    - **Density Check**: Do A and B co-occur? 
    - **Significance Check**: Are there strong verbs/tags?
    - *Result*: 
        - If Density < Threshold: **Skip LLM**. Clone `State(20)` -> `State(30)`.
        - If Density > Threshold: **Proceed**.

3.  **LLM Analysis (If Triggered)**:
    - **Input**: 
        - `Previous State`: `State(20).summary_so_far` + `unresolved_threads`
        - `New Events`: Summaries of Ch 21-30.
    - **Prompt**: "Update the relationship state based *only* on new events. Maintain consistency."
    - **Output**: `State(30)`.

4.  **Commit**:
    - `StateStore.save(State(30))`.

---

## 5. Implementation Roadmap

### Phase 1: Foundation (The Engine)
- [x] Define `BaseNarrativeState` and `RelationshipState` models.
- [x] Implement `StateStore` (JSON file backend).
- [x] Implement `NarrativeEvolutionEngine` skeleton.

### Phase 2: The Pilot (Relationship Logic)
- [x] Implement `RelationshipPlugin`.
- [x] Design the System Prompt for incremental analysis.
- [x] Implement "Adaptive Triggering" heuristic (Keyword matching).

### Phase 3: Integration
- [x] Connect to `analysis.py` API.
- [x] Verify with test cases (Ch 1-20).

### Phase 4: UI (The Arc Drawer)
- [x] Update frontend to fetch and visualize `RelationshipState` (Stages, Metrics).
- [x] Fix Timeline Sorting and State Ambiguity (v4.2).

---

## 6. Known Issues & Future Work
- **Summary Quality**: The `summary_so_far` field currently tends to reflect only the *latest* chapter's events rather than a true cumulative summary of the entire relationship history. This needs prompt engineering optimization.
- **Empty State filtering**: Backend now strictly filters out chapters with no interactions, but we need a better way to handle "internal psychological shifts" that happen without physical interaction.

---

## 7. Directory Structure Proposal
```
backend/
  narrative_engine/
    __init__.py
    core/
      engine.py          # The orchestrator
      store.py           # JSON/DB storage
      models.py          # Base Pydantic models
    plugins/
      base.py            # Plugin interface
      relationship.py    # The Pilot implementation
      world.py           # (Future)
    utils/
      trigger_logic.py   # Heuristics for adaptive triggering
```
