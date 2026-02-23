# Batch Relationship Analysis Tasks

## Backend Implementation
- [ ] **Refactor `jobs.py`**:
    - [ ] Import `ThreadPoolExecutor`.
    - [ ] Define `BatchRelationshipJobRequest` model.
- [ ] **Implement Orchestrator**:
    - [ ] Create `run_batch_analysis_orchestrator` function.
    - [ ] Implement `ThreadPoolExecutor` logic with `max_workers=3`.
    - [ ] Implement progress tracking (update parent job based on sub-task completion).
- [ ] **Add Endpoint**:
    - [ ] Implement `POST /api/jobs/batch-relationship`.

## Frontend Implementation
- [ ] **Create Component**:
    - [ ] `frontend/src/components/BatchAnalysisDialog.vue`: Dialog UI with table and selection logic.
- [ ] **Update GraphView**:
    - [ ] Add "Batch Analyze" button in `GraphView.vue`.
    - [ ] Implement logic to extract visible edges from `edgesDataSet`.
    - [ ] Integrate `BatchAnalysisDialog`.
- [ ] **API Client**:
    - [ ] Update `frontend/src/api.ts` to include `batchRelationshipAnalysis` method.

## Verification
- [ ] **Test Concurrency**: Verify only 3 tasks run at once.
- [ ] **Test Error Handling**: Verify batch continues even if one pair fails.
- [ ] **Test UI**: Verify dialog loads correct edges and progress updates.
