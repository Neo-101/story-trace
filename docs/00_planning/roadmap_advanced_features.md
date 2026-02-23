# Roadmap: Advanced Relationship Arc Visualization

**Status**: Planned / Future Feature
**Target**: v4.3 or later

## 1. Concept: Multi-Dimensional Arc Timeline
Currently, the relationship arc is presented as a list of key moments (cards) with a summary state. To better visualize the *evolution* of a relationship, we plan to introduce a quantitative timeline view.

## 2. Visualization Design
*   **X-Axis (Time)**:
    *   **Chapter Index**: Standard linear progression (Ch 1, Ch 2, ...).
    *   **Narrative Time** (Optional): If the novel has explicit timestamps/dates, map events to a real timeline.
*   **Y-Axis (Metrics)**:
    *   Normalized scale (0-100%) for relationship dimensions.
*   **Series (Lines)**:
    *   Three distinct lines superimposed on the same chart, distinguished by color:
        *   🔵 **Trust (信任)**
        *   🔴 **Romance (浪漫)**
        *   ⚔️ **Conflict (冲突)**

## 3. User Experience
*   **Interaction**: Hovering over a point on the line chart should highlight the corresponding chapter/event card in the existing list view (or show a tooltip).
*   **Toggle**: Users should be able to toggle individual lines on/off to focus on specific dimensions (e.g., just viewing the rise of Conflict).
*   **Integration**: This chart will be placed at the top of the `RelationshipArcDrawer`, above the "Latest State" summary.

## 4. Technical Requirements
*   **Frontend**:
    *   Library: Use `Chart.js` or `ECharts` (via Vue wrapper) for rendering.
    *   Data Source: The existing `RelationshipTimelineEvent` already contains `narrative_state` with these numeric values.
*   **Backend**:
    *   No major changes needed; data is already available in the `narrative_state` field of timeline events.
    *   Ensure `narrative_state` is consistently populated for all keyframes (handled by current `evolve_state` logic).

## 5. Value Proposition
*   Provides an immediate visual summary of the relationship's trajectory (e.g., "High trust initially, then a sudden drop in Ch 20, followed by rising conflict").
*   Helps identify key turning points (local maxima/minima) at a glance.
