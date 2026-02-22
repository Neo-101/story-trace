# Design Specification: Async Relationship Analysis & UI Integration

**Feature**: On-Demand Relationship Analysis with Background Processing
**Status**: Draft
**Target Version**: v4.3

---

## 1. Problem Definition
Users want to trigger the LLM-based "Relationship Arc" analysis directly from the Graph UI for any pair of entities.
**Constraints**:
1.  **Latency**: Analysis can take 30s - 5mins depending on chapter count. It must be non-blocking.
2.  **Cost/Noise**: We shouldn't analyze pairs with trivial interactions (e.g., met once).
3.  **UX**: User needs visibility on progress but shouldn't be locked into a modal.

---

## 2. Threshold Strategy: "Smart Default with User Override"

We need to filter out "noise" (insignificant relationships) while allowing user autonomy.

### 2.1 The Strategy
We reject the "Fixed Threshold" or "Pure User Setting" in favor of a **Smart Warning System**.

1.  **Hard Minimum (System enforced)**:
    *   **Rule**: Entities must co-occur in at least **2 distinct chapters**.
    *   **Reasoning**: A "Relationship Arc" (Change over time) requires at least two data points ($T_0$ and $T_1$). One interaction is just an event, not an arc.

2.  **Soft Threshold (Warning)**:
    *   **Rule**: `Interaction Count >= 3` OR `Co-occurrence >= 3 chapters`.
    *   **Behavior**:
        *   If `Score >= Soft Threshold`: Direct start.
        *   If `Score < Soft Threshold`: Show confirmation modal.
            > "Entities 'Sun Jack' and 'Passerby A' have only 2 interactions. Deep analysis may result in hallucinations or sparse data. Continue?"

3.  **Why this is better**:
    *   Avoids tedious configuration for 90% of cases.
    *   Prevents accidental clicks on weak edges.
    *   Allows "Power Users" to force analysis on subtle relationships.

---

## 3. Backend Architecture: Simple Async Job Manager

Since we want to avoid heavy dependencies (Redis/Celery) for this local-first tool, we will implement a lightweight **In-Memory Job Manager** within FastAPI.

### 3.1 Components
1.  **`JobManager` (Singleton)**:
    *   Stores `jobs: Dict[str, JobStatus]`.
    *   Methods: `submit_job()`, `get_job()`, `update_progress()`.
2.  **`JobStatus` Schema**:
    ```python
    class JobStatus(BaseModel):
        job_id: str
        type: str           # "relationship_analysis"
        status: str         # "pending", "processing", "completed", "failed"
        progress: int       # 0-100
        message: str        # "Analyzing Chapter 45/120..."
        result: Any         # The final timeline data (or error)
        created_at: float
    ```
3.  **`NarrativeEvolutionEngine` Update**:
    *   Add `on_progress` callback support to `analyze_relationship_incremental`.

### 3.2 API Endpoints
- `POST /api/jobs/relationship`:
    - Payload: `{ source: "A", target: "B", force: bool }`
    - Returns: `{ job_id: "uuid" }`
- `GET /api/jobs/{job_id}`: Long-polling or simple polling endpoint.
- `GET /api/jobs`: List active jobs.

---

## 4. Frontend UX: "Fire and Forget"

### 4.1 Interaction Flow
1.  **Selection**: User `Ctrl+Click` two nodes.
2.  **Action**: "Analyze Arc" button appears in the context menu/panel.
3.  **Validation**:
    *   Frontend checks `edge.weight` or `co_occurrence`.
    *   If low -> Show Warning Modal.
    *   If high -> Call API.
4.  **Feedback (The "Bubble")**:
    *   API returns `202 Accepted` + `job_id`.
    *   **Global Job Widget** (Bottom-Right) appears/updates.

### 4.2 The Job Widget (Floating Bubble)
- **Collapsed State (Default)**:
    - Small pill: `🔄 Analyzing Arc (45%)...`
    - Progress bar background.
- **Hover/Expanded State**:
    - Detailed list of active jobs.
    - "Analyzing Sun Jack <-> Song 6"
    - "Chapter 12/50: Identifying key events..."
    - [Cancel] button.
- **Completion State**:
    - Turns Green: `✅ Analysis Ready`
    - Click action: Opens `RelationshipArcDrawer` with the new data.

---

## 5. Implementation Roadmap

### Step 1: Backend Job Infrastructure
- [ ] Create `core/jobs.py` (JobManager).
- [ ] Update `NarrativeEvolutionEngine` to accept `progress_callback(current, total, msg)`.
- [ ] Implement `POST /api/jobs/relationship` endpoint using `BackgroundTasks`.

### Step 2: Frontend Job Store
- [ ] Create `stores/jobStore.ts` (Pinia).
- [ ] Implement polling logic (interval: 2s).

### Step 3: UI Integration
- [ ] Update `GraphView` to handle `Ctrl+Click` selection & Validation logic.
- [ ] Create `JobStatusWidget.vue` (The Bubble).
- [ ] Connect "View Result" to `RelationshipArcDrawer`.

---

## 6. Technical Considerations
- **Concurrency**: Since we use local/remote LLMs, we should limit to **1 concurrent analysis job** to avoid rate limits or freezing the computer. The `JobManager` should enforce a queue.
- **Persistence**: If the server restarts, jobs are lost. This is acceptable for v1.
- **Error Handling**: If LLM fails (502/Timeout), the job status becomes `FAILED` and the Bubble turns red with a retry button.
