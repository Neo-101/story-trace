# Module 1: Dynamic Relationship Arc (Detailed Plan)

**Status**: Implemented (Frontend Refactoring Phase)

## 1. Core Concept
Visualize the evolution of a relationship between two entities over time.
Instead of a static edge, show a **timeline of interactions**, revealing how the relationship changes (e.g., from "Stranger" to "Partner" to "Enemy").

## 2. User Interaction Flow
1.  **Selection**: 
    - User clicks Entity A (Source).
    - User clicks Entity B (Target).
    - Both nodes highlight; a "Compare / Relationship" floating action button appears.
2.  **View**:
    - User clicks "View Arc".
    - A dedicated drawer (`RelationshipArcDrawer`) opens on the right.
3.  **Visualization**:
    - **Header**: Avatar A <-> Avatar B.
    - **Body**: Vertical timeline of chapters where *both* entities appear or interact.
    - **Layout**: 3-Column Grid.
        - **Left**: A -> B interactions (Indigo).
        - **Center**: Timeline axis with chapter markers.
        - **Right**: B -> A interactions (Rose).
    - **Content**: For each interaction point, show the relation type and description.

## 3. Technical Implementation

### 3.1 Backend (`web_ui/routers/analysis.py`)
- **Endpoint**: `GET /api/novels/{...}/relationship?source={A}&target={B}`
- **Logic**:
  - Retrieve `AggregatedRelationship` from `EntityAggregator`.
  - **Bidirectional Search**: Check for `(A, B)` AND `(B, A)` relationships.
  - **Merge**: Combine timelines from both directions into a unified event list sorted by chapter.
  - **Output**: List of `RelationshipTimelineEvent` containing `interactions` with `direction` ("forward"/"backward").

### 3.2 Frontend (`frontend`)
- **API Client**: `fetchRelationshipTimeline` in `api/client.ts`.
- **Store**: `selectedNodes` state in `GraphView.vue`.
- **GraphView.vue**:
  - Manage selection state (max 2 nodes).
  - Show "View Arc" button when 2 nodes are selected.
- **RelationshipArcDrawer.vue**:
  - **Refactored Layout**:
    - Use CSS Grid `grid-cols-[1fr_2rem_1fr]` for precise alignment.
    - Visual distinction between Forward (Indigo, Right-aligned) and Backward (Rose, Left-aligned) interactions.
    - Connector lines linking cards to the central timeline axis.

## 4. Execution Steps
1.  [x] **Backend**: Implement API endpoint (handle bidirectional lookup).
2.  [x] **Frontend API**: Update client.
3.  [x] **Graph Interaction**: Implement selection logic.
4.  [x] **UI Component**: Refactor `RelationshipArcDrawer.vue` for bidirectional timeline layout.
