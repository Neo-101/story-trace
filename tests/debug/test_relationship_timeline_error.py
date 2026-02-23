import pytest
import os
from fastapi.testclient import TestClient
from backend.server import app
from sqlmodel import Session, create_engine, select
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, StoryRelationship

# --- Setup for Reproduction ---
# We need to mimic the exact request that failed in the screenshot:
# GET /api/novels/{novel}/{hash}/{timestamp}/relationship?source=...&target=...

client = TestClient(app)

def test_relationship_timeline_error_reproduction():
    """
    Attempt to reproduce the 500 error when fetching relationship timeline.
    This test will fail if the API returns 500.
    """
    # 1. Setup Data (or use existing if possible, but better to mock for stability)
    # But since we suspect the issue is with file system state (StateStore), 
    # we might need to actually invoke the code path that reads files.
    
    # Let's try to hit the API with dummy data first to see if it's a code logic error
    # vs a data error.
    
    # We need a valid session to inject data
    # For this debug test, we'll just try to call the function directly if possible,
    # or use the TestClient with a mocked DB session.
    
    # Actually, the error is likely in `_state_store.list_history` reading bad files.
    # Let's create a temporary directory with a bad file and try to read it using StateStore directly.
    
    from backend.narrative_engine.core.store import StateStore
    from backend.narrative_engine.core.models import RelationshipState
    import shutil
    from pathlib import Path
    
    # Setup Temp Cache
    test_cache_dir = Path("tests/debug/temp_cache")
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)
    
    store = StateStore(base_path=str(test_cache_dir))
    
    novel_hash = "test_hash"
    plugin_type = "relationship"
    entity_id = "A_B"
    
    # Create valid file
    store.save_state(novel_hash, plugin_type, entity_id, RelationshipState(
        chapter_index=1,
        entity_id=entity_id,
        summary_so_far="test summary",
        source="A",
        target="B",
        trust_score=0.5,
        romance_score=0.0,
        dynamics=[]
    ))
    
    # Create INVALID file that caused the crash
    # The crash was `int(f.stem.split("_")[1])`
    # So a file named "checkpoint_bad.json" or "DS_Store" would cause it.
    
    entity_dir = test_cache_dir / novel_hash / plugin_type / entity_id
    (entity_dir / "checkpoint_bad.json").touch()
    (entity_dir / ".DS_Store").touch()
    
    # Trigger the bug
    try:
        history = store.list_history(novel_hash, plugin_type, entity_id, RelationshipState)
        print(f"Successfully retrieved {len(history)} records.")
    except Exception as e:
        pytest.fail(f"StateStore.list_history crashed with: {e}")
    finally:
        # Cleanup
        if test_cache_dir.exists():
            shutil.rmtree(test_cache_dir)

if __name__ == "__main__":
    test_relationship_timeline_error_reproduction()
