# Bug Report: "View Arc" Button Missing

## Description
When selecting two nodes in the Graph View (using Shift + Click), the expected floating panel containing the "View Arc" (Relationship Arc) button does not appear.

## Steps to Reproduce
1. Open the Graph View (`/`).
2. Hold `Shift` key.
3. Click on Entity A.
4. Click on Entity B.
5. **Observed**: Both nodes appear selected visually (Vis.js highlighting), but the Vue-controlled floating panel (bottom center) does not render.
6. **Expected**: A panel showing "Compare Entity A & Entity B" and a "View Arc" button should appear.

## Potential Causes (Hypothesis)
1. **Vis.js Event Handling**: The `click` event in Vis.js might not be reporting `params.nodes` correctly during a multi-select operation, or the `multiselect` option isn't behaving as expected with the `click` event listener.
2. **Reactivity Issue**: The `selectedNodes` ref might not be triggering the `v-if` condition in the template, or the array update is not detected.
3. **CSS/Z-Index**: The panel might be rendered but hidden behind the canvas or other elements (though less likely given the `z-30` class).
4. **Selection Logic**: The logic `if (selectedIds.length === 2)` inside the click handler might be failing if `params.nodes` returns only the *last clicked* node instead of the *accumulated* selection.

## Severity
High (Blocks the new "Relationship Arc" feature).

## Status
Pending Analysis.
