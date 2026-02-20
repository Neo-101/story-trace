# Vibe Coding Refactor Roadmap (Remaining Tasks)

## 1. Core Experience Fixes (Highest Priority)
Before adding new features, we must ensure the base reading experience is flawless.
- [ ] **Fix Missing Original Text**: The "Reader View" currently shows summaries but fails to display the original novel content.
    - *Diagnosis*: Likely caused by `summaries.json` not containing the full text, which resides in separate `.txt` files.
    - *Plan*: Update migration script to ingest text from `chapters/*.txt` into the SQLite `content` column.
- [ ] **Fix Duplicate Chapters**: (Already identified, fix pending verification) Ensure index extraction is robust.

## 2. Interactive Visualization (Phase 2.5)
The current "Graph" tab is a placeholder. We need to bring the data to life.
- [x] **Implement `GraphView.vue`**:
    - Integration with `vis-network` or `d3.js`.
    - Features: Node merging, relationship filtering, click-to-navigate.
    - Added: Entity Details Panel, Type-based Coloring, Physics Toggle.
- [ ] **Dynamic Graph API**: Ensure the backend efficiently serves graph data for specific chapter ranges.

## 3. Performance & Polish (Phase 3)
- [ ] **Virtual Scrolling**: Implement `vue-virtual-scroller` for `OverviewGrid` to support novels with 2000+ chapters.
- [ ] **Streaming Responses**: (Optional) Use Server-Sent Events (SSE) for real-time AI generation feedback.

## 4. AI Assistant (Phase 4)
- [ ] **Chat-to-Novel**: RAG-based Q&A interface.
