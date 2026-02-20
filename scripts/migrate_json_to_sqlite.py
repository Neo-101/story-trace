import os
import sys
import json
import re
from pathlib import Path
from sqlmodel import Session, select, create_engine, SQLModel

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine, create_db_and_tables
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity, StoryRelationship

def extract_chapter_index(title: str, id_str: str, loop_index: int) -> int:
    # 1. Try to extract from title (e.g. "第123章", "Chapter 123")
    if title:
        # Match Chinese "第X章"
        match = re.search(r'第(\d+)章', title)
        if match:
            return int(match.group(1))
        
        # Match "Chapter X"
        match = re.search(r'Chapter\s*(\d+)', title, re.IGNORECASE)
        if match:
            return int(match.group(1))
            
    # 2. Try to extract from ID (e.g. "ch_123")
    if id_str and id_str.startswith('ch_'):
        try:
            return int(id_str.split('_')[1])
        except:
            pass
            
    # 3. Fallback
    return loop_index + 1

def migrate():
    create_db_and_tables()
    
    output_dir = Path("output")
    if not output_dir.exists():
        print("No output directory found.")
        return

    with Session(engine) as session:
        # Novel level
        for novel_dir in output_dir.iterdir():
            if not novel_dir.is_dir():
                continue
            novel_name = novel_dir.name
            print(f"Processing novel: {novel_name}")
            
            # Create/Get Novel
            novel = session.exec(select(Novel).where(Novel.name == novel_name)).first()
            if not novel:
                novel = Novel(name=novel_name)
                session.add(novel)
                session.commit()
                session.refresh(novel)
            
            # Hash level
            for hash_dir in novel_dir.iterdir():
                if not hash_dir.is_dir():
                    continue
                file_hash = hash_dir.name
                
                # Create/Get Version
                version = session.exec(select(NovelVersion).where(NovelVersion.novel_id == novel.id, NovelVersion.hash == file_hash)).first()
                if not version:
                    version = NovelVersion(novel_id=novel.id, hash=file_hash)
                    session.add(version)
                    session.commit()
                    session.refresh(version)
                
                # Timestamp level (Run)
                for run_dir in hash_dir.iterdir():
                    if not run_dir.is_dir():
                        continue
                    timestamp = run_dir.name
                    
                    # Check if run exists
                    run = session.exec(select(AnalysisRun).where(AnalysisRun.version_id == version.id, AnalysisRun.timestamp == timestamp)).first()
                    if run:
                        print(f"  Run {timestamp} already exists, skipping.")
                        continue
                    
                    # Create Run
                    # Try to read metadata
                    metadata_path = run_dir / "run_metadata.json"
                    config_snapshot = None
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                config_snapshot = f.read()
                        except:
                            pass
                            
                    run = AnalysisRun(version_id=version.id, timestamp=timestamp, config_snapshot=config_snapshot)
                    session.add(run)
                    session.commit()
                    session.refresh(run)
                    
                    # Read summaries
                    data = []
                    summaries_path_jsonl = run_dir / "summaries.jsonl"
                    summaries_path_json = run_dir / "summaries.json"
                    
                    if summaries_path_jsonl.exists():
                         with open(summaries_path_jsonl, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        data.append(json.loads(line))
                                    except:
                                        pass
                    elif summaries_path_json.exists():
                        with open(summaries_path_json, 'r', encoding='utf-8') as f:
                            try:
                                data = json.load(f)
                            except:
                                pass
                    
                    if not data:
                        print(f"  No summary data found for {timestamp}, skipping.")
                        continue

                    print(f"  Importing {len(data)} chapters for {timestamp}...")
                    
                    for i, chapter_data in enumerate(data):
                        chapter_title = chapter_data.get('chapter_title') or chapter_data.get('title') or f"Chapter {i+1}"
                        chapter_id_str = str(chapter_data.get('id', ''))
                        
                        # Priority: Explicit Index > Title > ID > Loop
                        idx = chapter_data.get('chapter_index')
                        if idx is None:
                            idx = extract_chapter_index(chapter_title, chapter_id_str, i)

                        # Try to load content from text file
                        content = chapter_data.get('content')
                        if not content:
                            # Strategy 1: Try exact title match (e.g. "第1章孫杰克.txt")
                            txt_path_title = run_dir / f"{chapter_title}.txt"
                            # Strategy 2: Try ID match (e.g. "ch_1.txt")
                            txt_path_id = run_dir / f"{chapter_id_str}.txt"
                            
                            if txt_path_title.exists():
                                try:
                                    with open(txt_path_title, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                except:
                                    pass
                            elif txt_path_id.exists():
                                try:
                                    with open(txt_path_id, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                except:
                                    pass

                        # Create Chapter
                        chapter = Chapter(
                            run_id=run.id,
                            chapter_index=idx,
                            title=chapter_title,
                            headline=chapter_data.get('headline'),
                            content=content
                        )
                        session.add(chapter)
                        session.commit()
                        session.refresh(chapter)
                        
                        # Summaries
                        for sent in chapter_data.get('summary_sentences', []):
                            summary = Summary(
                                chapter_id=chapter.id,
                                text=sent['summary_text']
                            )
                            spans = sent.get('source_spans', [])
                            if spans and len(spans) > 0:
                                summary.span_start = spans[0].get('start_index')
                                summary.span_end = spans[0].get('end_index')
                            
                            session.add(summary)
                            
                        # Entities
                        entities = chapter_data.get('entities', [])
                        # entities can be a list of dicts
                        for ent in entities:
                            if isinstance(ent, dict):
                                entity = Entity(
                                    chapter_id=chapter.id,
                                    name=ent.get('name', ''),
                                    type=ent.get('type', 'Unknown'),
                                    description=ent.get('description'),
                                    count=ent.get('count', 1)
                                )
                                session.add(entity)
                            
                        # Relationships
                        rels = chapter_data.get('relationships', [])
                        for rel in rels:
                            if isinstance(rel, dict):
                                relationship = StoryRelationship(
                                    chapter_id=chapter.id,
                                    source=rel.get('source', ''),
                                    target=rel.get('target', ''),
                                    relation=rel.get('relation', ''),
                                    description=rel.get('description', ''),
                                    weight=rel.get('weight', 1)
                                )
                                session.add(relationship)
                        
                        session.commit()

if __name__ == "__main__":
    migrate()
