# StoryTrace Architecture V2: Vibe Coding Refactor

## 1. Vision & Motivation
StoryTrace has evolved from a simple script collection into a complex system. The current "Patchwork" development model (HTML + Vanilla JS + Vue CDN) has reached its limits, leading to:
- **Fragile State Management**: Manual DOM manipulation and scattered refs (e.g., auto-scroll bugs).
- **Poor Developer Experience**: No types, no HMR, no component reusability.
- **UX Bottlenecks**: Blocking operations, lack of fluid interactions.

**Goal**: Transition to a **Modern, Engineering-First Architecture** that enables "Vibe Coding"—fluid, robust, and delightful user experiences with minimal friction.

## 2. Architecture Overview

### Frontend Stack (web_ui_v2)
- **Framework**: Vite + Vue 3 (SFC) + TypeScript
- **State Management**: Pinia (Store pattern for Novels, Chapters, Graph)
- **Styling**: Tailwind CSS (Utility-first)
- **Visualization**: Vis.js (encapsulated in Vue components)
- **Routing**: Vue Router (SPA navigation)

### Backend Services (Existing + Planned)
- **API**: FastAPI (Stateless, RESTful)
- **Database (Phase 2)**: SQLite/DuckDB (Replacing JSON files)
- **Real-time (Phase 3)**: WebSocket/SSE for progress streaming

## 3. Implementation Phases

### Phase 1: Engineering Foundation (Current Focus)
- [ ] **Scaffold**: Initialize `web_ui_v2` with Vite/TS.
- [ ] **Infrastructure**: Setup Tailwind, Pinia, Router, Axios.
- [ ] **API Layer**: Typed SDK for backend communication.
- [ ] **Component System**:
    - `OverviewGrid`: Virtualized card list with auto-scroll.
    - `ReaderView`: Immersive text reader with entity highlighting.
    - `GraphView`: Reactive graph visualization.
    - `AppShell`: Responsive layout and navigation.

### Phase 2: Data & Performance
- [ ] **Database Integration**: Migrate from JSON to SQLite.
- [ ] **Incremental Updates**: Smart merging of analysis results.

### Phase 3: "Vibe" Features
- [ ] **Streaming UI**: Typewriter effects for summaries.
- [ ] **Live Graph**: Dynamic node growth during analysis.
- [ ] **Chat-to-Novel**: RAG-based Q&A assistant.

## 4. Key Technical Decisions
- **Separation of Concerns**: UI components purely render data; Stores handle logic and API calls.
- **Virtualization**: Use `vue-virtual-scroller` (or similar) for the chapter list to handle 1000+ chapters smoothly.
- **Typed API**: Shared interfaces for `Chapter`, `Entity`, `GraphNode` to ensure frontend-backend contract.
