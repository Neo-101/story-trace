# Feature: Best-Effort Result Merging

## Problem
Currently, the system treats each run (identified by a timestamp) as an isolated dataset. If a user modifies the Prompt or Model configuration (even slightly), the fingerprint changes, invalidating previous caches. This forces users to re-run the entire novel to see a complete graph, even if 90% of the chapters were successfully processed in previous runs.

## Solution: Auto-Merging (Read Layer)
Instead of physically merging JSON files on disk, we implement a **Virtual Merge** logic at the API level. When the frontend requests graph data for a specific timestamp, the backend will:
1.  Load the `summaries.json` from the requested run.
2.  Scan all sibling directories (other timestamps for the same novel/file_hash).
3.  Identify missing chapters in the current run.
4.  Fill gaps using data from other runs (prioritizing recent runs).

## Implementation Details

### 1. `ResultMerger` Class
Located in `core/world_builder/merger.py`.

#### Logic
*   **Input**: `base_run_path` (The run selected by the user).
*   **Process**:
    1.  Load `base_summaries` from `base_run_path`.
    2.  Create a map: `chapter_id -> summary`.
    3.  Identify `missing_chapter_ids` (if we know the total chapter count, or just try to find *any* additional chapters).
    4.  Scan `output/{novel}/{hash}/*` directories.
    5.  Sort other runs by timestamp (descending).
    6.  For each other run:
        *   Load its `summaries.json`.
        *   For each chapter in it:
            *   If `chapter_id` is NOT in our map, add it.
            *   (Optional) Mark its source as "merged from {timestamp}".
    7.  Convert map values to list and sort by `chapter_id` (using integer parsing if possible).

### 2. API Integration
In `web_ui/routers/analysis.py`:
*   Replace direct file reading with `ResultMerger.merge_summaries(run_path)`.
*   This ensures `list_entities` and `get_graph_data` always return the most complete dataset available.

## Compatibility Considerations
*   **Data Structure**: We assume all `summaries.json` files follow the `ChapterSummary` Pydantic model. If a very old run has a different schema, `pydantic` validation might fail. We should wrap the loading in `try-except` and skip malformed files.
*   **Entity Consistency**: The `EntityAggregator` (with `aliases.json`) will handle entity name variations (e.g., "Robot" vs "Tapai") during the aggregation phase, so merging raw chapter summaries is safe.

## Future Enhancements
*   **UI Indicators**: Show which chapters came from different runs in the frontend.
*   **Manual Override**: Allow users to explicitly select which runs to merge.
