# Vibe Coding Parallel Development Guidelines

## 1. Backend Isolation (后端隔离)
- **Scope**: You are ONLY allowed to implement logic within your specific module aggregator (e.g., `concept_aggregator.py`).
- **Data Protocol First**: If your module introduces new fields, you MUST update `data_protocol/models.py` FIRST.
    - **Verify**: Ensure the new fields are defined in `Entity` or `Relationship` Pydantic models.
    - **Migration**: Verify that `scripts/migrate_json_to_sqlite.py` correctly handles these fields (serialization/deserialization).
- **Aggregator Logic**: When updating `core/world_builder/aggregator.py`, ensure your new field is correctly collected and passed to your module aggregator.
    - **Dependency Check**: Ensure dependent fields (like `chapter_index`) are available and correctly parsed.
- **Data**: Store your module data in the dedicated field of `ExtendedAggregatedEntity` (e.g., `concept_evolution`). DO NOT touch `description` or `type`.

## 2. Frontend Isolation (前端隔离)
- **Components**: You MUST implement your UI as a standalone component in `frontend/src/components/Entity/` (e.g., `ConceptEvolutionCard.vue`).
- **Integration**: You are ONLY allowed to insert your component into the `<template #modules>` slot of `GraphView.vue`. DO NOT modify the graph rendering logic.

## 3. Testing Mandate (测试红线)
- **TDD**: You MUST write/run your specific feature test (e.g., `tests/features/test_concept.py`) first.
- **Regression**: Before finishing, you MUST run `pytest tests/regression/test_core_features.py`. If it fails, you MUST revert your changes.