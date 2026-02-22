# Pending UX Issue: Auto-Scroll to Chapter Card in Overview

## Status
**Unresolved** (Multiple attempts failed)

## Symptom
In "Global Overview" mode (card grid view):
1.  Selecting a chapter (e.g., "Chapter 18") from the top dropdown menu updates the internal state (`selectedChapterId`).
2.  The corresponding card highlights visually (blue border).
3.  **Failure**: The page does not automatically scroll to bring the selected card into view. The user must manually scroll down to find it.

## Attempted Fixes
1.  **DOM ID Binding**: Added `:id="'card-' + chap.id"` to chapter cards in `index.html`.
2.  **Watcher Logic**: Added `watch(selectedChapterId)` in `app.js` to trigger `el.scrollIntoView({ behavior: 'smooth', block: 'center' })`.
3.  **Lifecycle Management**: Added `nextTick` to ensure DOM is rendered before scrolling.
4.  **Data Dependency**: Added `watch(chapters)` to retry scrolling after data load.
5.  **Cache Busting**: Appended `?v=2` to `app.js` script tag to force reload.

## Potential Root Causes (Hypothesis)
*   **Virtual Scrolling / Overflow Container**: The scroll command is being issued on the wrong container. `scrollIntoView` works relative to the viewport, but if the cards are inside a specific `div` with `overflow-y: auto` (which they are), and that container isn't the main document body, the behavior might be inconsistent or require scrolling the container explicitly.
*   **Vue Reactivity Timing**: The `chapters` array might be replacing object references entirely, causing DOM elements to be destroyed and recreated *after* the scroll command fires.
*   **Browser/CSS Behavior**: Conflicts with `sticky` headers or flex layout calculation.

## Next Steps (Deferred)
*   Investigate container-specific scrolling: `container.scrollTop = card.offsetTop`.
*   Debug with explicit `console.log` on element coordinates.
