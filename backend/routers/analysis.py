from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity, StoryRelationship
from backend.schemas import (
    ChapterPreview, ChapterDetail, EntityDetail, SummarySentence, SourceSpan,
    GraphData, GraphNode, GraphEdge, EdgeEvent, TimelineEvent, RelationshipTimelineEvent, RelationshipInteraction
)
from data_protocol.models import (
    ChapterSummary, 
    SummarySentence as ProtoSummarySentence, 
    Entity as ProtoEntity, 
    Relationship as ProtoRelationship, 
    TextSpan as ProtoTextSpan
)
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
             spans.append(ProtoTextSpan(text="", start_index=s.span_start, end_index=s.span_end))
        
        summaries.append(ProtoSummarySentence(
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

@router.get("/{novel_name}/{file_hash}/{timestamp}/chapters", response_model=List[ChapterPreview])
def list_chapters(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    # Note: We ignore the specific timestamp for listing chapters, 
    # instead returning the merged result of all runs for this hash.
    # This implements the "Best Effort Merge" logic.
    chapters = get_merged_chapters(session, novel_name, file_hash)
    
    return [
        ChapterPreview(
            id=str(c.id),
            title=c.title,
            headline=c.headline or "",
            has_summary=True
        )
        for c in chapters
    ]

@router.get("/{novel_name}/{file_hash}/{timestamp}/chapters/{chapter_id}", response_model=ChapterDetail)
def get_chapter_detail(novel_name: str, file_hash: str, timestamp: str, chapter_id: str, session: Session = Depends(get_session)):
    try:
        db_id = int(chapter_id)
        chapter = session.get(Chapter, db_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid chapter ID")
        
    if not chapter:
         raise HTTPException(status_code=404, detail="Chapter not found")
         
    summary = db_chapter_to_summary(chapter)
    
    # Convert Proto models to Schema models
    summary_sentences = [
        SummarySentence(
            summary_text=s.summary_text,
            source_spans=[SourceSpan(**span.dict()) for span in s.source_spans]
        )
        for s in summary.summary_sentences
    ]
    
    entities = [
        EntityDetail(
            name=e.name,
            type=e.type,
            description=e.description,
            confidence=e.confidence or 1.0
        )
        for e in summary.entities
    ]
    
    return ChapterDetail(
        id=str(chapter.id),
        title=chapter.title,
        headline=chapter.headline,
        content=chapter.content or "",
        summary_sentences=summary_sentences,
        entities=entities
    )

@router.get("/{novel_name}/{file_hash}/{timestamp}/entities", response_model=List[GraphNode])
def list_entities(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    # Use merged chapters for aggregation
    chapters = get_merged_chapters(session, novel_name, file_hash)
    
    # Aggregate
    summaries = [db_chapter_to_summary(c) for c in chapters]
    
    aggregator = EntityAggregator()
    aggregated_entities = aggregator.aggregate_entities(summaries)
    
    return [
        GraphNode(
            name=e.name,
            type=e.type,
            description=e.description,
            count=e.count,
            chapter_ids=e.chapter_ids,
            history=e.history
        )
        for e in aggregated_entities
    ]

@router.get("/{novel_name}/{file_hash}/{timestamp}/graph", response_model=GraphData)
def get_graph_data(novel_name: str, file_hash: str, timestamp: str, session: Session = Depends(get_session)):
    chapters = get_merged_chapters(session, novel_name, file_hash)
    summaries = [db_chapter_to_summary(c) for c in chapters]
    
    aggregator = EntityAggregator()
    entities = aggregator.aggregate_entities(summaries)
    relationships = aggregator.aggregate_relationships(summaries)
    
    # Pre-calculate chapter ID to index map for sorting
    # This ensures that 'chapter_ids' list in GraphNode is sorted by logical order, not just string order
    chap_id_to_index = {str(c.id).strip(): c.chapter_index for c in chapters}
    
    nodes = []
    for e in entities:
        # Sort chapter IDs by index
        # Ensure x is stripped string before lookup
        sorted_chapter_ids = sorted(e.chapter_ids, key=lambda x: chap_id_to_index.get(str(x).strip(), 999999))
        
        nodes.append(GraphNode(
            name=e.name,
            type=e.type,
            description=e.description,
            count=e.count,
            chapter_ids=sorted_chapter_ids,
            history=e.history
        ))
    
    edges = []
    for r in relationships:
        timeline_events = [
            EdgeEvent(
                chapter_id=str(item['chapter_id']).strip(),
                relation=item.get('relation'),
                description=item.get('description'),
                order=item.get('order', 0),
                weight=1 # Default weight per event
            )
            for item in r.timeline
        ]
        
        # Sort edge events by chapter index as well
        timeline_events.sort(key=lambda x: chap_id_to_index.get(x.chapter_id, 999999))
        
        edges.append(GraphEdge(
            source=r.source,
            target=r.target,
            weight=r.weight,
            timeline=timeline_events
        ))
    
    return GraphData(nodes=nodes, edges=edges)

@router.get("/{novel_name}/{file_hash}/{timestamp}/entity/{entity_name}/timeline", response_model=List[TimelineEvent])
def get_entity_timeline(novel_name: str, file_hash: str, timestamp: str, entity_name: str, session: Session = Depends(get_session)):
    """
    Get the chronological timeline of events for a specific entity.
    """
    chapters = get_merged_chapters(session, novel_name, file_hash)
    timeline_events = []
    
    aggregator = EntityAggregator()
    # Normalize input name for matching
    normalized_target_name = aggregator._normalize_text(entity_name)
    
    last_chapter_idx = -1
    
    for chapter in chapters:
        summary = db_chapter_to_summary(chapter)
        relevant_sentences = []
        entity_in_chapter = False
        
        # 1. Check explicit entities list (Strong Match)
        for e in summary.entities:
            if aggregator._normalize_text(e.name) == normalized_target_name:
                entity_in_chapter = True
                break
        
        # 2. Check sentences for mentions (Contextual Match)
        for sent in summary.summary_sentences:
            if normalized_target_name in sent.summary_text or entity_name in sent.summary_text:
                relevant_sentences.append(sent.summary_text)
                entity_in_chapter = True
        
        if entity_in_chapter:
            # Calculate gap (number of chapters skipped)
            gap = 0
            if last_chapter_idx != -1:
                gap = chapter.chapter_index - last_chapter_idx - 1
            
            # Use found sentences or fallback to entity description if available
            content = relevant_sentences
            if not content:
                # Try to find entity description
                for e in summary.entities:
                    if aggregator._normalize_text(e.name) == normalized_target_name and e.description:
                        content.append(e.description)
                        break
            
            timeline_events.append(TimelineEvent(
                chapter_id=str(chapter.id),
                chapter_title=chapter.title,
                content=content if content else ["本章提及该实体。"],
                gap_before=max(0, gap)
            ))
            
            last_chapter_idx = chapter.chapter_index
            
    return timeline_events

from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.engine import NarrativeEvolutionEngine
from backend.narrative_engine.plugins.relationship import RelationshipPlugin
from backend.narrative_engine.core.models import RelationshipState

# Initialize Narrative Engine (Lazy Singleton)
# In a real app, use dependency injection or app state
_state_store = StateStore()
_narrative_engine = NarrativeEvolutionEngine(_state_store)
_narrative_engine.register_plugin(RelationshipPlugin())

@router.get("/{novel_name}/{file_hash}/{timestamp}/relationship", response_model=List[RelationshipTimelineEvent])
def get_relationship_timeline(
    novel_name: str, 
    file_hash: str, 
    timestamp: str, 
    source: str, 
    target: str, 
    session: Session = Depends(get_session)
):
    """
    Get the interaction timeline between two entities (bidirectional).
    Returns a list of interactions where Source->Target OR Target->Source.
    Also returns the Narrative State (Trust, Romance, etc.) if available.
    """
    chapters = get_merged_chapters(session, novel_name, file_hash)
    timeline_events = []
    
    aggregator = EntityAggregator()
    norm_source = aggregator._normalize_text(source)
    norm_target = aggregator._normalize_text(target)
    
    if not norm_source or not norm_target:
        return []
    
    # Sort pair ID for consistent state lookup
    pair_id = "_".join(sorted([norm_source, norm_target]))
    
    # Pre-fetch states for all chapters (Optimization: List history once)
    # But for now, we just want to attach the state to the event.
    # Actually, we should evolve the state chapter by chapter here if we wanted real-time analysis.
    # But as per plan, we lazy load or just check if state exists.
    
    # To keep response fast, we WON'T trigger LLM here. 
    # We only read what's in the cache.
    # If the user wants to trigger analysis, they should call a POST endpoint (future).
    # OR: We trigger it but with a timeout/background task? 
    # Let's stick to "Read Only" for GET request to avoid blocking.
    
    # Optimization: Load all history for this pair once
    history = _state_store.list_history(file_hash, "relationship", pair_id, RelationshipState)
    state_map = {s.chapter_index: s for s in history}
    
    current_state = None
    
    for chapter in chapters:
        summary = db_chapter_to_summary(chapter)
        
        interactions = []
        
        for rel in summary.relationships:
            r_source = aggregator._normalize_text(rel.source)
            r_target = aggregator._normalize_text(rel.target)
            
            # Direction 1: A -> B
            if r_source == norm_source and r_target == norm_target:
                interactions.append(RelationshipInteraction(
                    direction="forward", 
                    relation=rel.relation,
                    description=rel.description,
                    confidence=rel.confidence
                ))
            
            # Direction 2: B -> A
            elif r_source == norm_target and r_target == norm_source:
                interactions.append(RelationshipInteraction(
                    direction="backward",
                    relation=rel.relation,
                    description=rel.description,
                    confidence=rel.confidence
                ))
        
        # Check if we have a narrative state for this chapter (or carried over)
        # In a perfect world, we'd have a state for every chapter.
        # Here we look for exact match or closest previous?
        # Let's check exact match first.
        narrative_state_dict = None
        if chapter.chapter_index in state_map:
            current_state = state_map[chapter.chapter_index]
        
        # If we have interactions OR a state update, we add an event
        if interactions or (current_state and current_state.chapter_index == chapter.chapter_index):
            
            # Serialize state if it belongs to this chapter
            if current_state and current_state.chapter_index == chapter.chapter_index:
                # We dump the state to dict
                narrative_state_dict = current_state.model_dump()

            timeline_events.append(RelationshipTimelineEvent(
                chapter_id=str(chapter.id),
                chapter_title=chapter.title,
                interactions=interactions,
                narrative_state=narrative_state_dict
            ))
            
    return timeline_events
