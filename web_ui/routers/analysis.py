from typing import List, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity, StoryRelationship
from data_protocol.models import ChapterSummary, SummarySentence, Entity as ProtoEntity, Relationship as ProtoRelationship, TextSpan
from core.world_builder.aggregator import EntityAggregator

router = APIRouter(prefix="/api/novels", tags=["analysis"])

def get_session():
    with Session(engine) as session:
        yield session

def db_chapter_to_summary(db_chapter: Chapter) -> ChapterSummary:
    # Convert summaries
    summaries = []
    for s in db_chapter.summaries:
        spans = []
        if s.span_start is not None and s.span_end is not None:
             spans.append(TextSpan(text="", start_index=s.span_start, end_index=s.span_end))
        
        summaries.append(SummarySentence(
            summary_text=s.text,
            source_spans=spans
        ))
    
    # Convert entities
    entities = []
    for e in db_chapter.entities:
        entities.append(ProtoEntity(
            name=e.name,
            type=e.type,
            description=e.description or "",
            confidence=1.0 
        ))

    # Convert relationships
    rels = []
    for r in db_chapter.relationships:
        rels.append(ProtoRelationship(
            source=r.source,
            target=r.target,
            relation=r.relation,
            description=r.description or "",
            confidence=1.0
        ))
    
    return ChapterSummary(
        chapter_id=str(db_chapter.id),
        chapter_title=db_chapter.title,
        headline=db_chapter.headline,
        summary_sentences=summaries,
        entities=entities,
        relationships=rels
    )

def get_merged_chapters(session: Session, novel_name: str, file_hash: str) -> List[Chapter]:
    """
    Best Effort Merge: Fetch all runs for this version and merge chapters.
    Later runs overwrite earlier ones for the same chapter index.
    """
    # 1. Find the version
    statement = select(NovelVersion).join(Novel).where(
        Novel.name == novel_name,
        NovelVersion.hash == file_hash
    )
    version = session.exec(statement).first()
    if not version:
        raise HTTPException(status_code=404, detail="Novel version not found")
    
    # 2. Get all runs sorted by timestamp (oldest first)
    # We want newer runs to overwrite older ones
    runs = sorted(version.runs, key=lambda r: r.timestamp)
    
    merged_map: Dict[int, Chapter] = {}
    
    for run in runs:
        for chapter in run.chapters:
            merged_map[chapter.chapter_index] = chapter
            
    # 3. Return sorted list
    return [merged_map[idx] for idx in sorted(merged_map.keys())]

@router.get("/{novel_name}/{file_hash}/{timestamp}/chapters")
def list_chapters(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    # Note: We ignore the specific timestamp for listing chapters, 
    # instead returning the merged result of all runs for this hash.
    # This implements the "Best Effort Merge" logic.
    chapters = get_merged_chapters(session, novel_name, file_hash)
    
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "headline": c.headline or "",
            "has_summary": True
        }
        for c in chapters
    ]

@router.get("/{novel_name}/{file_hash}/{timestamp}/chapters/{chapter_id}")
def get_chapter_detail(novel_name: str, file_hash: str, timestamp: str, chapter_id: str, session: Session = Depends(get_session)):
    try:
        db_id = int(chapter_id)
        chapter = session.get(Chapter, db_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid chapter ID")
        
    if not chapter:
         raise HTTPException(status_code=404, detail="Chapter not found")
         
    summary = db_chapter_to_summary(chapter)
    
    return {
        "id": str(chapter.id),
        "title": chapter.title,
        "headline": chapter.headline,
        "content": chapter.content or "",
        "summary_sentences": [s.dict() for s in summary.summary_sentences],
        "entities": [e.dict() for e in summary.entities]
    }

@router.get("/{novel_name}/{file_hash}/{timestamp}/entities")
def list_entities(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    # Use merged chapters for aggregation
    chapters = get_merged_chapters(session, novel_name, file_hash)
    
    # Aggregate
    summaries = [db_chapter_to_summary(c) for c in chapters]
    
    aggregator = EntityAggregator()
    aggregated_entities = aggregator.aggregate_entities(summaries)
    
    return aggregated_entities

@router.get("/{novel_name}/{file_hash}/{timestamp}/graph")
def get_graph_data(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    # Use merged chapters for graph
    chapters = get_merged_chapters(session, novel_name, file_hash)
    
    summaries = [db_chapter_to_summary(c) for c in chapters]
    
    aggregator = EntityAggregator()
    entities = aggregator.aggregate_entities(summaries)
    relationships = aggregator.aggregate_relationships(summaries)
    
    return {
        "nodes": entities,
        "edges": relationships
    }
