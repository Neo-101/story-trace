
import sys
import os
from sqlmodel import Session, select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, StoryRelationship, Entity

def inspect_data():
    with Session(engine) as session:
        # Get chapters 13-20 (Index 12-19)
        chapters = session.exec(select(Chapter).where(Chapter.chapter_index >= 12).order_by(Chapter.chapter_index)).all()
        
        print(f"Inspecting {len(chapters)} chapters (Index 12+)...")
        
        for ch in chapters:
            print(f"\n=== Chapter {ch.chapter_index + 1} (ID: {ch.id}) ===")
            
            # Check Relationships
            rels = session.exec(select(StoryRelationship).where(StoryRelationship.chapter_id == ch.id)).all()
            print(f"  Relationships: {len(rels)}")
            for r in rels:
                print(f"    R: {r.source} -> {r.target} (w={r.weight})")
                     
            # Check Entities
            ents = session.exec(select(Entity).where(Entity.chapter_id == ch.id)).all()
            print(f"  Entities: {len(ents)}")
            for e in ents:
                print(f"    E: {e.name} ({e.type})")

if __name__ == "__main__":
    inspect_data()
