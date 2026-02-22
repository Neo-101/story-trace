# Issue: Relationship Summary Quality

## Description
The user reported that the "Summary" field in the Relationship Arc analysis (Insights Panel) currently feels more like a "latest update log" rather than a comprehensive summary of the relationship so far.

> "目前的总结不像是总结，而是取了最近一次Arc有变化的章节的变化记录"

## Current Behavior
The `NarrativeEvolutionEngine` generates a `summary_so_far` field, but it seems biased towards the immediate changes in the analyzed chunk rather than aggregating the entire history.

## Expected Behavior
The summary should be a holistic overview of the relationship status up to the current point, integrating past context with recent developments.

## Proposed Solution (Future)
1. **Prompt Engineering**: Update the system prompt in `RelationshipPlugin` to explicitly instruct the LLM to maintain a running summary that evolves, rather than just describing the delta.
2. **Context Window**: Ensure enough historical context is passed to the LLM so it can synthesize the full picture.
3. **Separate Fields**: Consider splitting into `latest_update` (delta) and `relationship_overview` (cumulative).

## Priority
Medium (Enhancement)
