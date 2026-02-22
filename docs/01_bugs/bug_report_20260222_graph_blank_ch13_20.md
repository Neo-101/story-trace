# Bug Report: Graph View Blank Screen (Ch 13-20)

**Date**: 2026-02-22
**Status**: Fixed
**Severity**: High (Feature Blocking)

## 1. Issue Description
When navigating the Graph View timeline to Chapter 13 or later, the entire graph canvas would turn blank. The timeline slider would become unresponsive, and clicking "Next" would fail to advance the view.

- **Normal Range**: Ch 1-12
- **Abnormal Range**: Ch 13-20
- **Symptoms**: Blank canvas, unresponsive UI controls, `Vis.js` error in console.

## 2. Root Cause Analysis

### Initial Hypothesis (Disproven)
1. **Data Missing**: Suspected Chapter 13 data was missing from DB. -> **Disproven**: DB verification script showed full data.
2. **ID Type Mismatch**: Suspected `int` vs `str` mismatch in `chapter_id`. -> **Partially Relevant**, addressed by defensive coding, but not the root cause of the crash.

### Actual Cause: Duplicate Node IDs
The console revealed the smoking gun:
`Uncaught (in promise) Error: Cannot add item: item with id 治疗中心 already exists`

1. **Backend Aggregation Logic**:
   - The `EntityAggregator` grouped entities by `(name, type)`.
   - Entity "治疗中心" was classified as `Organization` in Ch 10, but as `Location` in Ch 12.
   - This resulted in **two distinct entity objects** in the API response:
     - `{ name: "治疗中心", type: "Organization" }`
     - `{ name: "治疗中心", type: "Location" }`

2. **Frontend Rendering**:
   - `GraphView.vue` generates Node IDs using `node.name` (e.g., `id: "治疗中心"`).
   - When both entities appeared in the filtered set (starting from Ch 13), Vis.js attempted to add two nodes with the same ID.
   - Vis.js threw a fatal error, halting the rendering loop and leaving the canvas blank.

## 3. Solution

### Backend Fix (`core/world_builder/aggregator.py`)
- **Change**: Modified aggregation grouping key from `(name, type)` to `name` (normalized).
- **Merge Strategy**: 
  - Types are tracked using a `Counter`.
  - The final entity type is determined by the most frequent type (Voting).
  - Descriptions and histories are merged into the single entity entry.

### Frontend Fix (`GraphView.vue`)
- **Defensive Coding**: Added a `Set` to track processed Node IDs during the update loop.
- **Action**: If a duplicate ID is encountered, it is skipped with a console warning, preventing the Vis.js crash even if backend data is dirty.

## 4. Verification
- **Reproduction Script**: `reproduce_graph_conflict.py` confirmed 6 entities had conflicting types (e.g., "塔派" as Person/Item).
- **Post-Fix**: Script confirmed 0 conflicts. Frontend graph renders correctly up to Chapter 20.

## 5. Lessons Learned
- **Entity Identity**: In a graph where nodes are identified by name, **Name** must be the sole unique constraint. Type is an attribute, not part of the identity.
- **Defensive Rendering**: Frontend visualization libraries (like Vis.js) are fragile to duplicate IDs. Always sanitize data before passing it to the library.
