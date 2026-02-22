# Product Roadmap: Advanced Narrative Intelligence (Phase 4+)

This document outlines the strategic vision for evolving StoryTrace from a "visualization tool" to a "narrative intelligence platform."

## Core Philosophy
Shift focus from **Entity-Centric** (who is who) to **Relation-Centric** (how they interact) and **World-Centric** (where they live).

## Module 1: Dynamic Relationship Arc (Dual Timeline)
**Status**: Planned (High Priority)
**Concept**: Visualizing the evolution of a relationship between two entities over time. Not just "they are connected," but "how their connection changed."
**Value**: Uncovers character dynamics like "Enemies to Lovers," "Betrayal," "Mentorship."

## Module 2: Progressive World Building (Concept Archeology)
**Status**: Planned (Medium Priority)
**Concept**: Tracking how the reader's understanding of key concepts/locations evolves.
**Value**: Visualizes the "fog of war" in storytelling. Shows how a "Simple Village" becomes "The Eye of the Formation" as plot reveals occur.

## Module 3: Narrative Threads & Foreshadowing (Chekhov's Gun)
**Status**: Planned (Low Priority)
**Concept**: Tracking the lifecycle of key items/events from "Introduction" -> "Active" -> "Resolution" -> "Forgotten."
**Value**: Helps authors close loops; helps readers find missed clues.

## Module 4: Faction Heatmap (Geopolitical Dynamics)
**Status**: Planned (Low Priority)
**Concept**: Color-coding the graph based on organizational affiliation to show power shifts.
**Value**: Turns the graph into a dynamic map of political/military influence.

---

# Strategic Architecture: The "Unified Narrative State Machine" (Layer 2+)

**Core Philosophy**: "One Engine, Many Stories."

As we analyze "Character Dynamics", "World Building", "Foreshadowing", and "Factions", we realize they share a fundamental pattern:
**They are all Time-Series State Tracking problems.**
Whether it's two people falling in love, a village becoming a battlefield, or a gun being fired, the underlying mechanism is identical:
`State(N) = LLM(State(N-1) + NewEvents(N))`

Instead of building 4 separate modules, we will build **One Unified Evolution Engine** with 4 specialized **Plugins**.

## 1. The Common Abstraction
We define a universal **Narrative Entity** that evolves over **Time Blocks**.

| Feature | The "Subject" | The "State" Schema (Snapshot) | The "Transition" Logic |
| :--- | :--- | :--- | :--- |
| **Relationship Arc** | Pair `(A, B)` | `{ trust_level, romance_level, power_dynamic, key_tags }` | "How did their interaction change?" |
| **World Building** | Location/Concept `L` | `{ knowledge_level, mystery_status, known_facts, danger_level }` | "What new secrets were revealed?" |
| **Narrative Threads** | Item/Event `I` | `{ status (intro/active/resolved), current_owner, significance }` | "Who holds the item? Is it used?" |
| **Faction Heatmap** | Organization `F` | `{ power_level, territory_list, key_members, active_conflicts }` | "Did they gain land or lose members?" |

## 2. The Unified Architecture
We will implement a single **`NarrativeEvolutionEngine`** that handles the heavy lifting:
1.  **State Management**: Loading previous snapshots, saving new ones.
2.  **Context Assembly**: Combining `State(N-1)` with `ChapterSummary(N)`.
3.  **LLM Orchestration**: Calling the LLM with the correct "Plugin Prompt".
4.  **Delta Calculation**: Detecting significant changes to notify the UI.

### 2.1 The "Plugin" System
Each feature becomes a configuration file (or class) defining:
- **Target Selector**: "Which entities to track?" (e.g., "Top 10 Characters" or "Locations > 5 mentions")
- **State Schema**: "What fields to track?" (Pydantic Model)
- **System Prompt**: "How to analyze the change?"

## 3. Benefits of Unification
- **Single Caching Strategy**: Solving the "Incremental Analysis" problem once solves it for all 4 modules.
- **Shared UI Components**: A generic "Timeline Drawer" can visualize *any* state change (Trust curve, Mystery curve, Power curve).
- **Cross-Module Insight**: The engine can eventually correlate states (e.g., "Faction Power dropped *because* Character A betrayed Character B").

---

# Detailed Design: Dynamic Relationship Arc (Module 1 - Implementation)
*This module will serve as the "Pilot" for the Unified Engine.*

## 1. User Experience (UX)

## 1. User Experience (UX)

### Entry Point
- **Graph View**: 
  - User holds `Shift` + Clicks Node A, then Node B.
  - Or, right-clicks an edge -> "View Relationship Timeline."
- **Entity Details**:
  - In Node A's details panel, a list of "Key Relationships." Clicking one opens the arc.

### Interface (The "Dual Helix" View)
A dedicated drawer or modal split into three columns:

| Column | Content | Visual Style |
| :--- | :--- | :--- |
| **Left** | **Entity A (Subject)** | Avatar + Name (e.g., "Sun Jieke") |
| **Center** | **Interaction Timeline** | Vertical line with nodes. Nodes represent shared chapters. |
| **Right** | **Entity B (Object)** | Avatar + Name (e.g., "Song 6") |

### Interaction Cards (Center Column)
Each node on the center line expands into a card:
- **Header**: Chapter 5: "The Deal"
- **Relation Tag**: `Client` -> `Mercenary` (Arrow indicates direction or mutual status)
- **Summary**: A snippet summarizing *only* their interaction in this chapter.
- **Sentiment**: Color-coded (Red=Hostile, Green=Friendly, Gray=Neutral).

## 2. Data Requirements

### Backend API
- **Endpoint**: `GET /api/novels/{...}/relationship?source={A}&target={B}`
- **Logic**:
  1. Retrieve `AggregatedRelationship` between A and B.
  2. Iterate through `relationship.timeline`.
  3. For each event in timeline:
     - Fetch Chapter Title.
     - Extract the specific `description` of the relationship in that chapter.
     - (Optional) Analyze sentiment of the description.

### Data Structure (Response)
```json
{
  "source": "Sun Jieke",
  "target": "Song 6",
  "timeline": [
    {
      "chapter_id": "5",
      "chapter_title": "The Deal",
      "relation": "Employer", // How A sees B
      "description": "Sun Jieke hires Song 6 for protection.",
      "sentiment": "neutral"
    },
    {
      "chapter_id": "20",
      "chapter_title": "Betrayal",
      "relation": "Enemy",
      "description": "Song 6 reveals he was working for the corp.",
      "sentiment": "negative"
    }
  ]
}
```

## 3. Technical Feasibility
- **Existing Foundation**: We already store `timeline` in `AggregatedRelationship` (added in v6).
- **Gap**: We need to expose this via a dedicated API and build the specific UI component.
- **Complexity**: Low. Data is ready; mostly frontend work.

## 4. Next Steps
1.  Implement backend API to fetch relationship timeline.
2.  Design `RelationshipArcDrawer.vue` (similar to `EntityChronicleDrawer`).
3.  Add interaction in `GraphView` to select two nodes.

---

# Strategic Architecture: Incremental Analysis & Caching (Layer 2+)

**Core Philosophy**: "Never Analyze the Same Chapter Twice."

As we move to high-cost, high-latency features (Relationship Dynamics, Arc Analysis), we must adopt an **Incremental Analysis Strategy**. 
The system should treat the novel not as a monolith, but as a growing sequence of immutable blocks.

## 1. The Problem: Repetitive Costs
- **Scenario**: User analyzes Ch 1-20. Later, user analyzes Ch 1-100.
- **Waste**: Without caching, the system re-reads and re-analyzes Ch 1-20 to build the relationship context for Ch 21-100.
- **Impact**: 
  - **Cost**: Double LLM tokens for the first 20 chapters.
  - **Time**: High latency for "updating" the graph.

## 2. The Solution: Checkpoint & Delta Architecture

### 2.1 Granular Caching (The "Block" Model)
We treat analysis results as **Blocks** tied to specific Chapter Ranges.

- **Level 1 Cache (Chapter)**: `ChapterSummary` (Already implemented).
- **Level 2 Cache (Relationship Segment)**: 
  - Store "Micro-Dynamics" for a pair (A, B) within a specific range (e.g., `rel_A_B_ch1_20.json`).
  - Contains: Interaction list, sentiment scores, local state (e.g., "A trusts B: 0.2").

### 2.2 Incremental Synthesis (The "Zipper" Logic)
When requesting an analysis for Ch 1-100:
1.  **Check Cache**: Do we have `Analysis(Ch 1-20)`? -> Yes.
2.  **Delta Computation**: Only run LLM analysis for Ch 21-100.
    - *Crucial Context*: Feed the *final state* of Ch 20 (e.g., "Status: Hostile") as the *initial state* for the Ch 21 prompt.
3.  **Merge**: Combine `Result(1-20)` + `Result(21-100)`.
4.  **Update Cache**: Save `Result(21-100)` and potentially `Result(1-100)` if it's a stable milestone.

## 3. Implementation Plan for Relationship Dynamics

### Step 1: State Snapshotting
- Define a schema for **Relationship State** at any chapter `N`.
  - Example: `{"trust_level": 50, "dominant_archetype": "Rival", "key_events": [...]}`.
- Save this snapshot alongside the `Timeline` data.

### Step 2: Contextual Chaining (Adaptive Triggering)
Instead of blindly feeding "Summary(N)" for every single chapter, we implement **Adaptive Event Density Triggering**:

1.  **Lightweight Scan (Local)**:
    - Before calling the LLM, the system scans the `ChapterSummary` for Ch 21-40 locally.
    - It checks for **Interaction Density**: "Do A and B actually appear/interact in this chapter?"
    - It checks for **Significance Keywords**: "Are there strong emotional verbs (betray, kiss, kill)?"

2.  **Dynamic Batching**:
    - **Scenario A (Low Activity)**: Ch 21-29 have 0 interactions. 
      - *Action*: Skip LLM. Extend the `State(20)` snapshot to Ch 29.
    - **Scenario B (High Activity)**: Ch 30 has a major fight.
      - *Action*: Trigger LLM for Ch 30, feeding `State(20)` as context.
    - **Scenario C (Accumulation)**: Ch 31-35 have minor dialogue.
      - *Action*: Aggregate Ch 31-35 into a single "Batch Prompt" and update state once.

3.  **Cost Efficiency**: 
    - LLM is only invoked when "something actually happens."
    - 99 trivial chapters = 0 LLM calls.
    - 1 pivotal chapter = 1 LLM call.

### Step 3: Lazy Evaluation
- Do **not** pre-calculate high-level arcs for all pairs.
- Trigger calculation **only** when the user clicks "View Arc" for a specific pair.
- Check database/cache for existing segments before calling LLM.

## 4. Value
- **Scalability**: Analyzing Ch 1000 costs the same as analyzing Ch 1 (assuming linear context growth is managed).
- **Responsiveness**: Immediate results for previously analyzed segments.
- **Cost Control**: Zero wasted tokens on re-runs.
