# Bug Report: Batch Analysis "View Result" Interaction Issue

**Date**: 2026-02-23
**Status**: Pending Design Decision
**Component**: Frontend (GraphView, JobStatusWidget)

## 1. Issue Description
After completing a "Batch Relationship Analysis" (processing multiple pairs simultaneously), the user is presented with a "View Result" (green) button in the notification toast.
*   **Expected Behavior**: Clicking the button should allow the user to see the results of the analysis.
*   **Actual Behavior**: Clicking the button currently does nothing visible or fails to open the expected view because the current event handler (`handleAnalysisResult` in `GraphView.vue`) hardcodes a check for `selectedNodes.length === 2`. Since batch analysis doesn't select nodes, this condition fails.

## 2. Technical Root Cause
The event handler in `GraphView.vue`:
```typescript
const handleAnalysisResult = (e: CustomEvent) => {
    // BUG: This restricts opening the result drawer to only single-pair manual analysis
    if (selectedNodes.value.length === 2) {
         openRelationshipDrawer();
    }
};
```
When a batch job finishes, the `result` payload contains summary data (e.g., total count, list of pairs), not a single `pair_id` to open.

## 3. Proposed Solutions & Open Questions

We are currently hesitating between two UX approaches for handling the "View Result" click after a batch job:

### Option A: Auto-Refresh Graph (Subtle)
*   **Behavior**: Clicking "View Result" simply re-fetches the graph data from the backend.
*   **Visual Feedback**: The edges that were analyzed will appear (or become thicker/colored) in the main graph view.
*   **Pros**: 
    *   Simple to implement.
    *   Keeps the user in the "Overview" mode.
*   **Cons**: 
    *   User might not notice what changed.
    *   Doesn't directly show the *content* of the analysis (the narrative arcs).

### Option B: Results List Dialog (Explicit)
*   **Behavior**: Clicking "View Result" opens a modal/dialog listing all the pairs that were just analyzed.
*   **Content**: A list like:
    *   `[Person] 孙杰克 - [Org] 塔派` [View Arc Button]
    *   `[Person] 宋6PUS - [Person] 金刚` [View Arc Button]
*   **Pros**: 
    *   Clear confirmation of what was done.
    *   Direct navigation to specific results.
*   **Cons**: 
    *   More UI work (new component).
    *   Another popup to dismiss.

## 4. Current Decision
**Defer Implementation**. We will pause fixing this specific interaction detail to focus on other priorities. The functionality of batch analysis itself works (data is generated), but the "View Result" shortcut is currently broken for batch jobs.

## 5. Next Steps (When Resumed)
1.  Decide between Option A and Option B.
2.  Refactor `GraphView.vue`'s `handleAnalysisResult` to handle `BatchJobResult` payloads.
3.  If Option B, create `BatchResultsDialog.vue`.
