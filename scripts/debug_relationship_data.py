import sys
import os
from sqlmodel import Session, select
from typing import List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.engine import engine
from core.db.models import Novel, NovelVersion, Chapter
from core.world_builder.aggregator import EntityAggregator
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.models import RelationshipState
from backend.routers.analysis import get_merged_chapters, db_chapter_to_summary

def debug_relationship_data(novel_name: str, file_hash: str, source: str, target: str):
    print(f"DEBUG: Analyzing relationship between '{source}' and '{target}' in '{novel_name}' ({file_hash})")
    
    with Session(engine) as session:
        chapters = get_merged_chapters(session, novel_name, file_hash)
        print(f"DEBUG: Found {len(chapters)} merged chapters.")
        
        aggregator = EntityAggregator()
        norm_source = aggregator._normalize_text(source)
        norm_target = aggregator._normalize_text(target)
        print(f"DEBUG: Normalized: '{norm_source}' <-> '{norm_target}'")
        
        # Check State Store
        pair_id = "_".join(sorted([norm_source, norm_target]))
        state_store = StateStore()
        history = state_store.list_history(file_hash, "relationship", pair_id, RelationshipState)
        print(f"DEBUG: Found {len(history)} cached states.")
        state_map = {s.chapter_index: s for s in history}
        
        for chapter in chapters:
            summary = db_chapter_to_summary(chapter)
            interactions = []
            
            for rel in summary.relationships:
                r_source = aggregator._normalize_text(rel.source)
                r_target = aggregator._normalize_text(rel.target)
                
                # Direction 1: A -> B
                if r_source == norm_source and r_target == norm_target:
                    interactions.append(rel)
                
                # Direction 2: B -> A
                elif r_source == norm_target and r_target == norm_source:
                    interactions.append(rel)
            
            has_state = chapter.chapter_index in state_map
            
            # Print status for each chapter
            if interactions or has_state:
                status = []
                if interactions: status.append(f"Interactions({len(interactions)})")
                if has_state: status.append("State")
                
                print(f"Chapter {chapter.chapter_index}: {', '.join(status)}")
                
                if interactions:
                    for i, rel in enumerate(interactions):
                        print(f"  - Int {i+1}: {rel.source}->{rel.target} [{rel.relation}] '{rel.description}'")
            
            # Verify Filter Logic
            if interactions:
                pass # This would PASS the filter
            else:
                # This would FAIL the filter (be hidden)
                # But user says it is showing.
                # If we print it here, it means it has NO interactions but HAS state?
                # Wait, the filter is `if interactions:`.
                # So if interactions is empty, it should NOT be added.
                pass

if __name__ == "__main__":
    # Parameters from previous context
    NOVEL_NAME = "故障烏託邦"
    # Need to find hash dynamically or hardcode if known
    # From previous context: "8771c958" was mentioned in path, but let's look up DB
    
    with Session(engine) as session:
        novel = session.exec(select(Novel).where(Novel.name == NOVEL_NAME)).first()
        if not novel:
            print(f"Error: Novel {NOVEL_NAME} not found")
            sys.exit(1)
        
        # Pick the latest version
        version = novel.versions[-1]
        FILE_HASH = version.hash
        print(f"Using hash: {FILE_HASH}")

    SOURCE = "孙杰克"
    TARGET = "宋6PUS"
    
    debug_relationship_data(NOVEL_NAME, FILE_HASH, SOURCE, TARGET)
