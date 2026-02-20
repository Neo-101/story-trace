# Pending Bug: Duplicate Chapters in Merged View

## Symptom
When viewing the chapter list in the frontend, some chapters appear multiple times and out of order (e.g., Chapter 11 appearing after Chapter 14).

## Root Cause Analysis
The "Best Effort Merge" logic relies on `chapter_index` to identify and merge identical chapters across different runs.
The current issue stems from **inconsistent index assignment** during the migration process:
1.  **Inconsistent Source Data**: Different runs (full vs partial) might produce different metadata structures.
2.  **Fallback Logic Failure**: When explicit `chapter_index` is missing, the migration script falls back to:
    *   Parsing ID (`ch_XX`) - Reliable if ID is correct.
    *   Loop Counter (`i + 1`) - **Unreliable** for partial runs. If a run only contains chapters 11-20, the loop counter assigns indices 1-10, causing collisions or displacement.

## Proposed Fix: Robust Index Extraction
To ensure consistent indexing regardless of run context, we must implement a **Multi-Stage Strategy** for determining `chapter_index`:

1.  **Priority 1: Explicit Field** - Use `chapter_index` from JSON if valid.
2.  **Priority 2: Title Parsing (New)** - Extract integer from Chinese numerals or digits in `title` (e.g., "第11章" -> 11). This is the most semantically correct anchor.
3.  **Priority 3: ID Parsing** - Extract integer from `id` (e.g., "ch_11" -> 11).
4.  **Priority 4: Fallback** - Use loop counter only as a last resort, and log a warning.

## Action Plan
1.  **Update Migration Script**: Implement `extract_chapter_index` function with title parsing logic.
2.  **Reset Database**: Clear existing dirty data.
3.  **Re-Migrate**: Run the updated script to regenerate the database with correct indices.
