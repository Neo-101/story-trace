# Vibe Coding Parallel Development Guidelines

## 1. Backend Isolation (后端隔离)
- **Scope**: You are ONLY allowed to implement logic within your specific module aggregator (e.g., `concept_aggregator.py`).
- **Prohibited**: DO NOT modify `data_protocol/models.py` or `core/world_builder/aggregator.py` core logic without explicit permission.
- **Data**: Store your module data in the dedicated field of `ExtendedAggregatedEntity` (e.g., `concept_evolution`). DO NOT touch `description` or `type`.

## 2. Frontend Isolation (前端隔离)
- **Components**: You MUST implement your UI as a standalone component in `frontend/src/components/Entity/` (e.g., `ConceptEvolutionCard.vue`).
- **Integration**: You are ONLY allowed to insert your component into the `<template #modules>` slot of `GraphView.vue`. DO NOT modify the graph rendering logic.

## 3. Testing Mandate (测试红线)
- **TDD**: You MUST write/run your specific feature test (e.g., `tests/features/test_concept.py`) first.
- **Regression**: Before finishing, you MUST run `pytest tests/regression/test_core_features.py`. If it fails, you MUST revert your changes.