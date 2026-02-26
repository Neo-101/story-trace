
import sys
import os
from sqlmodel import Session, select, delete

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, Entity, StoryRelationship, Summary

def fix_chapter_77():
    print("=== 正在修复第 77 章数据 ===")
    with Session(engine) as session:
        # 1. 查找所有第 77 章
        chapters = session.exec(select(Chapter).where(Chapter.chapter_index == 77)).all()
        
        if not chapters:
            print("✅ 未找到第 77 章记录，无需清理。")
            return

        print(f"⚠️ 发现 {len(chapters)} 条第 77 章记录，准备删除...")
        
        for ch in chapters:
            print(f"   - 删除 Chapter ID: {ch.id}, Title: {ch.title}")
            
            # 级联删除关联数据 (虽然 Entities/Rels 可能为 0，但 Summary 可能存在)
            # Delete Summaries
            session.exec(delete(Summary).where(Summary.chapter_id == ch.id))
            # Delete Entities
            session.exec(delete(Entity).where(Entity.chapter_id == ch.id))
            # Delete Relationships
            session.exec(delete(StoryRelationship).where(StoryRelationship.chapter_id == ch.id))
            # Delete Chapter itself
            session.delete(ch)
            
        session.commit()
        print("🎉 清理完成！请重新运行 'python app/main.py' (带 --repair 77) 以重新生成数据。")

if __name__ == "__main__":
    fix_chapter_77()
