# Project Optimization & LLM Collaboration Enhancement Plan

## 1. Problem Diagnosis: Why Collaboration Quality is Dropping

After reviewing the project structure and recent interaction history, I have identified three core issues affecting the quality of LLM collaboration:

### A. The "Split-Brain" Context Problem
*   **Symptom**: The project currently maintains two competing frontend structures:
    *   `web_ui/` (Legacy: Jinja2 templates, vanilla JS, `graph.js`).
    *   `web_ui_v2/` (Modern: Vue 3, TypeScript, Vite).
*   **Impact**: When you ask the LLM to "fix the graph", it has to decide between `web_ui/static/js/graph.js` and `web_ui_v2/src/components/GraphView.vue`. This consumes context window (tokens) and increases the probability of hallucination or applying fixes to the wrong file.
*   **LLM View**: To an LLM, both look like "valid active code".

### B. Cognitive Load & Token Noise
*   **Symptom**: The `docs/` folder is growing with every feature (`design_doc_v1` to `v10`).
*   **Impact**: While documentation is good, "stale" design docs clutter the context. The LLM spends resources processing V1 designs that are no longer relevant to V10 implementation.
*   **LLM View**: Hard to distinguish "Historical Record" from "Current Specification".

### C. Backend/Frontend Boundary Blurring
*   **Symptom**: The backend (`web_ui/server.py`) still contains logic to serve static files and templates for the legacy frontend, mixed with the new API endpoints.
*   **Impact**: This makes the backend "noisy". Pure API changes risk breaking legacy views, and vice versa.

---

## 2. Strategic Optimization Plan

To restore "Vibe Coding" efficiency and clarify LLM interactions, I propose a **"Clean Slate Architecture"** refactor.

### Phase 1: Context Hygiene (The "Declutter")
*   **Action 1: Archive Legacy Frontend**.
    *   Move `web_ui/static/` and `web_ui/templates/` to a `legacy_archive/` folder outside the main workspace or zip them.
    *   **Benefit**: The LLM will *only* see `web_ui_v2` as the frontend. No more confusion between `graph.js` and `GraphView.vue`.
*   **Action 2: Consolidate Documentation**.
    *   Create a single `System_Architecture.md` that describes the *current* state.
    *   Move `design_doc_v1` through `v9` to `docs/archive/`. Keep only active feature specs.
    *   **Benefit**: Reduces context usage by ~40%.

### Phase 2: Explicit Architecture (The "Map")
*   **Action 3: Rename for Clarity**.
    *   Rename `web_ui` (Python backend) to `backend` or `api_server`.
    *   Rename `web_ui_v2` to `frontend` or `web_app`.
    *   **Benefit**: Semantic naming helps the LLM understand the role of each directory immediately (`backend/routers` vs `frontend/components`).
*   **Action 4: Create `LLM_CONTEXT.md`**.
    *   A specific file meant for *me* (the LLM) to read. It contains:
        *   "We are using Vue 3 + Pinia + Tailwind."
        *   "We are using FastAPI + SQLModel."
        *   "Do not use Jinja2."
        *   "Current Focus: Feature X."

### Phase 3: "Vibe Engineering" Standards
*   **Action 5: Type-First Contract**.
    *   Enforce a rule: Before writing logic, update `types/index.ts` (Frontend) and `schemas.py` (Backend).
    *   **Benefit**: This creates a clear "Interface Contract". The LLM is much better at implementing logic when the data shape is strictly defined first.

---

## 3. Immediate Execution Roadmap (Proposed)

1.  **Refactor Directory Structure**:
    ```text
    /
    ├── backend/          (Was web_ui, stripped of static files)
    ├── frontend/         (Was web_ui_v2)
    ├── core/             (Shared logic, unchanged)
    ├── docs/             (Active docs only)
    │   └── archive/      (Old docs)
    └── scripts/
    ```
2.  **Update `main.py`**: Point it to serve the compiled `frontend/dist` or just run as API server (letting Vite handle dev server).
3.  **Fix the Bug**: With a clean context, debugging the "View Arc" button will be straightforward (likely a Vis.js event mapping issue).

## 4. Why This Helps YOU (The User)
*   **Higher Quality Answers**: I won't get distracted by old code.
*   **Faster Response**: Less context to read = faster processing.
*   **Stability**: Clear separation means frontend bugs won't crash the backend.

---

*Ready to proceed with Phase 1 (Archiving & Renaming) before fixing the bug?*
