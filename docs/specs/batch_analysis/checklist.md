# QA Checklist for Batch Analysis

## Functional Testing
- [ ] **Filter Integration**:
    - [ ] Adjust "Min Interactions" slider.
    - [ ] Click "Batch Analyze".
    - [ ] Verify dialog only shows edges meeting the criteria.
- [ ] **Batch Execution**:
    - [ ] Select 5+ pairs.
    - [ ] Start analysis.
    - [ ] Verify backend logs show max 3 concurrent tasks.
    - [ ] Verify progress bar updates smoothly (0% -> 20% -> ... -> 100%).
- [ ] **Results**:
    - [ ] Verify all selected pairs have updated relationship arcs.
    - [ ] Verify graph updates after batch completion.

## Edge Cases
- [ ] **Empty Selection**: User opens dialog but selects nothing -> "Start" should be disabled.
- [ ] **Single Pair**: Batch analysis with 1 pair should work same as single analysis.
- [ ] **API Failure**: Simulate LLM failure for one pair -> Batch should finish with partial success.
