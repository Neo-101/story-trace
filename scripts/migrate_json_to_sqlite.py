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

from core.identifiers import IdentifierGenerator

def extract_chapter_index(title: str, id_str: str, loop_index: int) -> int:
    # 0. 优先尝试从 ID 中解析 ch_XX (使用统一的 IdentifierGenerator)
    idx = IdentifierGenerator.parse_chapter_index(id_str)
    if idx is not None:
        return idx
            
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
    
    # 2. Fallback
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
                            # 如果从标题解析失败（例如返回了默认的 i+1），尝试用 ID 解析
                            # 因为 extract_chapter_index 内部如果标题没匹配到，会尝试 ID，最后才是 Loop
                            # 但这里的逻辑是混合的。
                            # 更好的逻辑是：
                            # 1. 如果 chapter_data 中有 'chapter_index'，直接用
                            # 2. 如果没有，解析 title 中的数字
                            # 3. 如果没有，解析 id 中的数字 (ch_XX)
                            # 4. 如果都没有，使用 loop index (i+1)
                        
                        # 强制修正逻辑：如果 idx 远大于 loop index (例如 idx=100, i=19)，且 title 中包含 "第20章"
                        # 这可能是因为 regex 匹配到了错误的数字，或者 id 包含了非连续的数字
                        # 但对于增量更新，i 只是当前批次的索引，不能完全信任 i+1
                        
                        # 根本问题是 extract_chapter_index 可能会匹配到错误的数字，或者 chapter_id_str 是乱序的
                        # 比如 id="100" (数据库ID) 但实际是第20章
                        
                        # 让我们优化 extract_chapter_index 的调用方式
                        # 如果 chapter_data 没有 index，我们优先信任 title
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
