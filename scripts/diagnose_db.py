
import sys
import os
from sqlmodel import Session, select, func

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, Entity, StoryRelationship

def diagnose():
    with Session(engine) as session:
        chapters = session.exec(select(Chapter).order_by(Chapter.chapter_index)).all()
        
        print(f"{'Index':<5} | {'ID':<5} | {'Entities':<8} | {'Rels':<5} | {'Title'}")
        print("-" * 60)
        
        for ch in chapters:
            ent_count = session.exec(select(func.count()).where(Entity.chapter_id == ch.id)).one()
            rel_count = session.exec(select(func.count()).where(StoryRelationship.chapter_id == ch.id)).one()
            
            print(f"{ch.chapter_index:<5} | {ch.id:<5} | {ent_count:<8} | {rel_count:<5} | {ch.title}")

if __name__ == "__main__":
    diagnose()
