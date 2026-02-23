# Optimization Plan: Narrative Engine (Phase 2)

Based on the recent implementation of the async relationship analysis system, we have identified several areas for optimization to improve maintainability, robustness, and cost-efficiency.

## 🎯 Priority 1: High (Immediate Action)

### 1. Unified Data Contracts (Type Safety)
- **Problem**: Inconsistent data structures (dictionaries vs objects) between `jobs.py` and `plugins` led to `KeyError` bugs.
- **Solution**: Define strict Pydantic models for internal data passing.
- **Action Items**:
  - [ ] Create `AnalysisEvent` model in `core/models.py`.
  - [ ] Update `jobs.py` to construct `AnalysisEvent` objects.
  - [ ] Update `plugins/relationship.py` to accept `List[AnalysisEvent]`.

### 2. Prompt Management (Maintainability)
- **Problem**: Hardcoded prompts in plugin logic make iteration difficult and code cluttered.
- **Solution**: Extract prompts into a dedicated module or template file.
- **Action Items**:
  - [ ] Create `backend/narrative_engine/prompts.py`.
  - [ ] Move the relationship analysis prompt template to this new module.
  - [ ] Refactor `RelationshipPlugin.generate_prompt` to use the new template.

## 🎯 Priority 2: Medium (Next Steps)

### 3. Smart Context Compression (Token Efficiency)
- **Problem**: Sending all sentences in a chapter can be wasteful if interactions are sparse.
- **Solution**: Pre-filter context before sending to LLM.
- **Action Items**:
  - [ ] Implement a "Relevance Filter" in `jobs.py` or `engine.py`.
  - [ ] Only include sentences with high semantic relevance to the entity pair.

### 4. Rolling Summary (Long-term Context)
- **Problem**: `summary_so_far` grows indefinitely, potentially exceeding context windows.
- **Solution**: Periodic summarization of the summary.
- **Action Items**:
  - [ ] Implement a `summarize_history` method in `RelationshipPlugin`.
  - [ ] Trigger summarization every N chapters (e.g., 10).

## 🎯 Priority 3: Low (Future Enhancements)

### 5. Structured Output (Reliability)
- **Problem**: LLM JSON output can be malformed.
- **Solution**: Use `instructor` or provider-specific JSON mode/Function Calling.
- **Action Items**:
  - [ ] Update `LLMClient` to support structured output mode.
  - [ ] Define Pydantic models for expected LLM responses.

### 6. Resilience (Error Handling)
- **Problem**: Failures in one chapter stop the analysis flow or are just skipped.
- **Solution**: Retry mechanism for transient errors.
- **Action Items**:
  - [ ] Implement retry decorator for LLM calls.
  - [ ] Add Dead Letter Queue for failed analysis tasks.
