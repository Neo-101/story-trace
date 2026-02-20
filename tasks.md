# StoryTrace Development Tasks

## Phase 6.9: Graph Optimization & Simplification (Global Mode)

### Problem
The "Cumulative" (Global) graph is too cluttered and confusing:
- Edge labels show chapter-specific sequence numbers (e.g., `[2]`) which duplicate across chapters.
- Too many nodes and edges make the graph unreadable.
- Lack of filtering controls.

### Requirements
1.  **Simplify Global Mode**: Provide a high-level summary view.
2.  **Remove Detail**: Hide sequence numbers and specific interaction labels in Global Mode.
3.  **Edge Aggregation**: Merge interactions into weighted edges (thickness = frequency).
4.  **Node Filtering**: Allow users to hide low-frequency nodes and specific entity types.

### Tasks
- [x] **Refactor Graph Logic (`graph.js`)**
    - [x] Modify `updateFilter` to support distinct rendering styles for `focus` vs `cumulative`.
    - [x] **Global Mode**:
        - [x] Set edge `label` to `undefined` (hidden).
        - [x] Set edge `title` (tooltip) to show interaction count (e.g., "5 interactions").
        - [x] Adjust edge `width` scaling (e.g., `Math.log(weight) * scale`).
    - [x] **Focus Mode**:
        - [x] Keep existing detailed labels (`[1] 遇见`).
        - [x] Keep existing width logic.

- [x] **Add UI Controls (`index.html` / `app.js`)**
    - [x] Add "Min Interactions" Slider (Range: 1-10, Default: 1).
    - [x] Add "Entity Type" Checkboxes (Person, Location, Organization, Item, Concept, Other).
    - [x] Bind controls to Vue state (`minWeight`, `visibleTypes`).

- [x] **Implement Filtering Logic (`graph.js`)**
    - [x] Update `updateFilter` to accept `minWeight` and `visibleTypes` parameters.
    - [x] Filter edges: Only show edges with `weight >= minWeight`.
    - [x] Filter nodes: Only show nodes where `type` is in `visibleTypes` AND (node has visible edges OR node value >= minWeight).

- [ ] **Testing & Verification**
    - [ ] Verify Global Mode is cleaner and labels are gone.
    - [ ] Verify Focus Mode still shows details.
    - [ ] Verify slider hides weak connections.
    - [ ] Verify checkboxes hide unwanted entity types.
