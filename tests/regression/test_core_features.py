import pytest
import json
import os
from pathlib import Path
from data_protocol.models import ChapterSummary

# --- Regression Test Suite ---
# Goal: Ensure new modules (Concept, Clue, Faction) do NOT break existing core data structures.

# Use Real Novel Data as Golden Master
REAL_DATA_PATH = Path("output/故障烏託邦/8771c958/20260222_111350/summaries.json")
GOLDEN_MASTER_PATH = Path("tests/regression/data/golden_master_real.json")

def load_real_data():
    if not REAL_DATA_PATH.exists():
        pytest.skip(f"Real data not found at {REAL_DATA_PATH}. Please run the pipeline first.")
    with open(REAL_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_golden_master():
    if not GOLDEN_MASTER_PATH.exists():
        return None
    with open(GOLDEN_MASTER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_golden_master(data):
    GOLDEN_MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN_MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def test_real_data_integrity():
    """
    Regression Test:
    Load the REAL novel data and ensure it still validates against the current Protocol.
    This ensures that our Protocol changes haven't broken backward compatibility with existing data.
    """
    data_list = load_real_data()
    
    # Try to parse the first chapter using the current Pydantic model
    # If this fails, it means we broke compatibility!
    first_chapter_data = data_list[0]
    
    # Validate against ChapterSummary model
    try:
        summary = ChapterSummary(**first_chapter_data)
        assert summary.chapter_title == "第1章孫杰克"
        assert len(summary.entities) > 0
    except Exception as e:
        pytest.fail(f"Failed to validate real data against Protocol: {e}")

def test_golden_master_comparison():
    """
    Regression Test: Golden Master
    Compare the structure of the real data against a saved snapshot.
    """
    current_data = load_real_data()
    golden_data = load_golden_master()
    
    if golden_data is None:
        # First run: Establish baseline from the real data
        save_golden_master(current_data)
        pytest.skip("Golden Master created from real data. Run again to verify.")
    
    # Compare Chapter 1
    curr_ch1 = current_data[0]
    gold_ch1 = golden_data[0]
    
    # Check for missing keys (Breaking Changes)
    curr_keys = set(curr_ch1.keys())
    gold_keys = set(gold_ch1.keys())
    
    missing_keys = gold_keys - curr_keys
    assert not missing_keys, f"Breaking Change! Missing keys in real data: {missing_keys}"
    
    # Check data consistency
    assert curr_ch1["headline"] == gold_ch1["headline"]
