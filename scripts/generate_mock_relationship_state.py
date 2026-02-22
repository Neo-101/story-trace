import sys
import os
import random
from sqlmodel import Session, select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, StoryRelationship, Novel, NovelVersion, AnalysisRun
from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.models import RelationshipState
from backend.narrative_engine.plugins.relationship import RelationshipPlugin

def generate_mock_data(novel_name: str, file_hash: str, source_name: str, target_name: str):
    """
    Generates mock RelationshipState checkpoints for a specific pair.
    """
    store = StateStore() # Uses default cache/narrative path
    plugin = RelationshipPlugin()
    
    # Normalize names for ID (simple version)
    pair_id = "_".join(sorted([source_name, target_name]))
    
    print(f"Generating mock states for {pair_id} in {novel_name} ({file_hash})...")
    
    with Session(engine) as session:
        # Get novel, version, run
        # Try to find novel by name if provided
        novel = session.exec(select(Novel).where(Novel.name == novel_name)).first()
        if not novel:
            print(f"Novel '{novel_name}' not found. Trying first available...")
            novel = session.exec(select(Novel)).first()
            if not novel:
                print("No novel found in DB.")
                return
        
        print(f"Using Novel: {novel.name} (ID: {novel.id})")
            
        version = session.exec(select(NovelVersion).where(NovelVersion.novel_id == novel.id, NovelVersion.hash == file_hash)).first()
        if not version:
            print(f"Version '{file_hash}' not found for novel {novel.name}.")
            # Try finding any version
            version = session.exec(select(NovelVersion).where(NovelVersion.novel_id == novel.id)).first()
            if version:
                print(f"Falling back to version: {version.hash}")
            else:
                return
            
        # Get latest run
        run = session.exec(select(AnalysisRun).where(AnalysisRun.version_id == version.id).order_by(AnalysisRun.timestamp.desc())).first()
        if not run:
            print("No run found.")
            return
            
        # Get chapters
        chapters = session.exec(select(Chapter).where(Chapter.run_id == run.id).order_by(Chapter.chapter_index)).all()
        
        if not chapters:
            print("No chapters found in DB.")
            return

        # Initial State
        current_state = plugin.get_initial_state(pair_id)
        current_state.source = source_name
        current_state.target = target_name
        
        # Simulation loop
        for i, chapter in enumerate(chapters):
            # 1. Check if they interact in this chapter
            rels = session.exec(select(StoryRelationship).where(
                StoryRelationship.chapter_id == chapter.id,
                ((StoryRelationship.source == source_name) & (StoryRelationship.target == target_name)) |
                ((StoryRelationship.source == target_name) & (StoryRelationship.target == source_name))
            )).all()
            
            if rels:
                print(f"  Ch {chapter.chapter_index}: Interaction found! Updating state...")
                
                # Update metrics randomly to simulate evolution
                current_state.trust_level = max(0, min(100, current_state.trust_level + random.randint(-10, 15)))
                current_state.conflict_level = max(0, min(100, current_state.conflict_level + random.randint(-5, 10)))
                
                if current_state.trust_level > 80:
                    current_state.dominant_archetype = "Partner"
                    current_state.current_stage = "Deep Trust"
                elif current_state.trust_level < 30:
                    current_state.dominant_archetype = "Enemy"
                    current_state.current_stage = "Open Conflict"
                else:
                    current_state.dominant_archetype = "Acquaintance"
                
                current_state.summary_so_far += f"\n[Ch {chapter.chapter_index}] They interacted ({len(rels)} times)."
                current_state.chapter_index = chapter.chapter_index
                
                # SAVE CHECKPOINT
                store.save_state(file_hash, "relationship", current_state)
            
    print("Done! Checkpoints saved to cache.")

if __name__ == "__main__":
    # Change these to match your actual DB data
    NOVEL_NAME = "仙剑奇侠传" # Replace with actual novel name in DB
    FILE_HASH = "d41d8cd98f00b204e9800998ecf8427e" # Replace with actual hash
    SOURCE = "李逍遥"
    TARGET = "林月如"
    
    if len(sys.argv) > 4:
        NOVEL_NAME = sys.argv[1]
        FILE_HASH = sys.argv[2]
        SOURCE = sys.argv[3]
        TARGET = sys.argv[4]
        
    generate_mock_data(NOVEL_NAME, FILE_HASH, SOURCE, TARGET)
