# Module 1: Dynamic Relationship Arc (Detailed Plan)

## 1. Core Concept
Visualize the evolution of a relationship between two entities over time.
Instead of a static edge, show a **timeline of interactions**, revealing how the relationship changes (e.g., from "Stranger" to "Partner" to "Enemy").

## 2. User Interaction Flow
1.  **Selection**: 
    - User holds `Shift` key in Graph View.
    - Clicks Entity A (Source).
    - Clicks Entity B (Target).
    - Both nodes highlight; a "Compare / Relationship" floating action button appears.
2.  **View**:
    - User clicks "View Relationship Arc".
    - A dedicated drawer (`RelationshipArcDrawer`) opens on the right.
3.  **Visualization**:
    - **Header**: Avatar A <-> Avatar B.
    - **Body**: Vertical timeline of chapters where *both* entities appear or interact.
    - **Content**: For each interaction point, show the specific sentence/summary describing their dynamic.

## 3. Technical Implementation

### 3.1 Backend (`web_ui/routers/analysis.py`)
- **New Endpoint**: `GET /api/novels/{...}/relationship?source={A}&target={B}`
- **Logic**:
  - Retrieve `AggregatedRelationship` from `EntityAggregator`.
  - **Bidirectional Search**: Check for `(A, B)` AND `(B, A)` relationships.
  - **Merge**: Combine timelines from both directions (if directed edges exist) or just return the undirected timeline.
  - **Filter**: Return list of `{ chapter_id, relation, description, weight }`.

### 3.2 Frontend (`web_ui_v2`)
- **API Client**: Add `fetchRelationshipTimeline` to `api/client.ts`.
- **Store**: Add `selectedNodes` state to `useNovelStore` (or local state in `GraphView`).
- **GraphView.vue**:
  - Listen for `click` events with `event.event.srcEvent.shiftKey`.
  - Manage selection state (max 2 nodes).
  - Show "View Relationship" button when 2 nodes are selected.
- **RelationshipArcDrawer.vue**:
  - New component, similar to `EntityChronicleDrawer`.
  - Props: `sourceEntity`, `targetEntity`, `timeline`.
  - Layout: Dual-header, central timeline.

## 4. Execution Steps
1.  **Backend**: Implement API endpoint (handle bidirectional lookup).
2.  **Frontend API**: Update client.
3.  **Graph Interaction**: Implement Shift+Click selection logic.
4.  **UI Component**: Build the Drawer.
