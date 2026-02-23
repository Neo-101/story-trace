
# Bug Report: Graph View Blank & Relationship Arc Crash (Post-Refactor)

**Date**: 2026-02-23
**Status**: Fixed
**Severity**: High (Feature Blocking)

## 1. Issue Description
After the major architecture refactoring (unifying `data_protocol`, `db`, `api` models), two critical issues appeared in the Web UI:
1. **Graph View Blank**: The main graph visualization failed to load, showing a 500 Internal Server Error.
2. **Relationship Arc Crash**: Clicking "View Arc" on an edge resulted in a 500 error and a blank panel.

## 2. Root Cause Analysis

### Issue 1: Graph View Blank
- **Error**: `sqlite3.OperationalError: no such column: entity.confidence`
- **Cause**: The database schema in `core/db/models.py` was updated to include a `confidence` field (inheriting from `BaseEntity`), but the existing SQLite database file (`storytrace.db`) was not migrated to reflect this change.
- **Fix**: Manually executed SQL `ALTER TABLE` commands to add the missing `confidence` column to both `entity` and `storyrelationship` tables.

### Issue 2: Relationship Arc Crash
- **Error**: `pydantic.ValidationError` in `get_relationship_timeline`.
- **Cause**: The `RelationshipInteraction` model inherits from `BaseRelationship`, which strictly requires `source` and `target` fields. The API endpoint code was constructing `RelationshipInteraction` objects without providing these mandatory fields, assuming only `direction`, `relation`, etc., were needed.
- **Fix**: Updated `backend/routers/analysis.py` to explicitly pass `source` and `target` from the underlying relationship data when creating `RelationshipInteraction` objects.

## 3. Solution

### Database Schema Fix
- **Action**: Ran `fix_db_schema.py` to add columns:
  ```sql
  ALTER TABLE entity ADD COLUMN confidence FLOAT;
  ALTER TABLE storyrelationship ADD COLUMN confidence FLOAT;
  ```

### Backend Code Fix (`backend/routers/analysis.py`)
- **Change**: Updated `get_relationship_timeline` to populate `source` and `target` fields in `RelationshipInteraction`.

## 4. Verification
- **Graph View**: `repro_sqlite_graph.py` confirmed successful data retrieval and graph construction.
- **Relationship Arc**: `repro_arc_error.py` confirmed successful retrieval of 11 interaction events for "孙杰克" & "宋6PUS".
- **User Feedback**: Confirmed graph is normal, but reported a new issue with Overview.

## 5. Next Steps
- **Overview Bug**: The user reported a bug in the Overview section. This will be handled in a new session to maintain context hygiene.
