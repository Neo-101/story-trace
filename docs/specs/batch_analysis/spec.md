# Batch Relationship Analysis Specification

## 1. Overview
Allow users to perform batch analysis of relationship arcs for multiple entity pairs simultaneously. This feature addresses the tediousness of analyzing pairs one by one.

## 2. User Flow
1.  **Filter**: User adjusts "Min Interactions" slider and "Entity Type" checkboxes in the Graph View to filter visible nodes/edges.
2.  **Initiate**: User clicks a new "Batch Analyze" button in the "FILTERS & LEGEND" panel.
3.  **Select**: A dialog appears listing all **visible edges** (pairs) that match the current filter criteria.
    *   Columns: Source, Target, Interaction Count, Status.
    *   Default: Select all (or top N).
4.  **Execute**: User clicks "Start Batch Analysis".
5.  **Monitor**: The UI shows a global progress bar for the batch job.
    *   "Analyzing 1/5: A & B..."
6.  **Complete**: Notifications appear as pairs are completed. The graph updates automatically.

## 3. Technical Architecture

### 3.1 Backend (Python/FastAPI)
*   **Concurrency Model**: Use `ThreadPoolExecutor` with `max_workers=3` to manage concurrency without blocking the main thread, respecting API rate limits.
*   **API Endpoint**:
    *   `POST /api/jobs/batch-relationship`
    *   Request Body: `BatchRelationshipJobRequest` containing a list of `RelationshipJobRequest`.
*   **Job Management**:
    *   Create a **Parent Job** ID for the batch.
    *   The Parent Job tracks the overall progress (completed pairs / total pairs).
    *   Sub-tasks run in the thread pool.
    *   **Orchestrator**: A background task that submits sub-tasks to the executor and updates the parent job status.

### 3.2 Frontend (Vue 3)
*   **Component**: `BatchAnalysisDialog.vue` (New).
    *   Props: `visibleEdges` (from Vis.js dataset).
    *   Features: Table with checkboxes, "Select All", "Start" button.
*   **Integration**: `GraphView.vue`.
    *   Add "Batch Analyze" button to the control panel.
    *   Extract visible edges using `edgesDataSet.get({ filter: ... })`.
    *   Pass data to the dialog.
*   **Store**: Update `useJobStore` to handle batch job status (if necessary, or reuse existing polling).

## 4. Data Structures

### Backend
```python
class BatchRelationshipJobRequest(BaseModel):
    novel_name: str
    file_hash: str
    pairs: List[Dict[str, str]] # [{"source": "A", "target": "B"}, ...]
    force: bool = False
```

### Frontend
```typescript
interface BatchPair {
  id: string; // edge id
  source: string;
  target: string;
  weight: number; // interaction count
  selected: boolean;
}
```

## 5. Constraints
*   **Concurrency**: Max 3 parallel LLM calls to avoid OpenRouter rate limits.
*   **Error Handling**: Individual pair failures should not fail the entire batch. Failed pairs should be reported in the final result.
