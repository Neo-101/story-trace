from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity, StoryRelationship
from backend.schemas import (
    ChapterPreview, ChapterDetail, EntityDetail, SummarySentence, SourceSpan,
    GraphData, GraphNode, GraphEdge, EdgeEvent, TimelineEvent, RelationshipTimelineEvent,
    RelationshipInteraction, ConceptAnalysisRequest
)
import json
from data_protocol.models import (
    ChapterSummary, 
    SummarySentence as ProtoSummarySentence, 
    Entity as ProtoEntity, 
    Relationship as ProtoRelationship, 
    TextSpan as ProtoTextSpan,
    ConceptStage # Import ConceptStage
)
from core.world_builder.aggregator import EntityAggregator
from backend.routers.analysis_helper import get_merged_chapters, db_chapter_to_summary, get_entity_timeline_logic
from backend.narrative_engine.plugins.concept import ConceptAnalyzer
from core.summarizer.llm_client import ClientFactory
from core.config import settings

router = APIRouter(prefix="/api/novels", tags=["analysis"])

def get_session():
    with Session(engine) as session:
        yield session

# Removed inline db_chapter_to_summary and get_merged_chapters as they are now in analysis_helper

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
    summary_sentences = []
    chapter_content = chapter.content or ""

    for s in summary.summary_sentences:
        spans = []
        for span in s.source_spans:
            if isinstance(span, dict):
                spans.append(SourceSpan(**span))
            else:
                # Extract text from content if empty (common for DB-stored summaries)
                span_text = span.text
                if not span_text and chapter_content and span.start_index is not None and span.end_index is not None:
                    span_text = chapter_content[span.start_index:span.end_index]
                
                spans.append(SourceSpan(
                    text=span_text,
                    start_index=span.start_index,
                    end_index=span.end_index
                ))
                
        summary_sentences.append(SummarySentence(
            summary_text=s.summary_text,
            source_spans=spans
        ))
    
    entities = []
    for e in summary.entities:
        entities.append(EntityDetail(
            name=e.name,
            type=e.type,
            description=e.description,
            confidence=e.confidence or 1.0
        ))
    
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
        
        # Attach concept_evolution from ExtendedAggregatedEntity if available
        concept_evolution = getattr(e, 'concept_evolution', None)

        nodes.append(GraphNode(
            name=e.name,
            type=e.type,
            description=e.description,
            count=e.count,
            chapter_ids=sorted_chapter_ids,
            history=e.history,
            concept_evolution=concept_evolution
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
    if not chapters:
        return []
        
    return get_entity_timeline_logic(chapters, entity_name)

@router.post("/{novel_name}/{file_hash}/analyze/concept", response_model=List[ConceptStage])
def analyze_concept(
    novel_name: str, 
    file_hash: str, 
    request: ConceptAnalysisRequest,
    session: Session = Depends(get_session)
):
    """
    Triggers on-demand Concept Evolution Analysis for a specific entity.
    Reads the Entity Chronicle (Timeline) and uses LLM to identify stages (Rumor/Fact/Truth).
    Updates the database with the results.
    """
    print(f"DEBUG: analyze_concept called for {novel_name}, entity={request.entity_name}")
    # Initialize LLM Client
    # Check for OpenRouter API Key
    try:
        if settings.OPENROUTER_API_KEY:
             llm_client = ClientFactory.create_client(
                 provider="openrouter",
                 api_key=settings.OPENROUTER_API_KEY,
                 model=settings.OPENROUTER_MODEL
             )
        else:
             # Fallback to Local LLM
             llm_client = ClientFactory.create_client(
                 provider="local",
                 base_url=settings.LOCAL_LLM_BASE_URL,
                 model=settings.LOCAL_LLM_MODEL
             )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM client: {e}")
    
    analyzer = ConceptAnalyzer(session, llm_client)
    stages = analyzer.analyze_entity(novel_name, file_hash, request.entity_name, force=request.force)
    
    return stages

from backend.narrative_engine.core.store import StateStore
from backend.narrative_engine.core.engine import NarrativeEvolutionEngine
from backend.narrative_engine.plugins.relationship import RelationshipPlugin
from backend.narrative_engine.core.models import RelationshipState

# Initialize Narrative Engine (Lazy Singleton)
# In a real app, use dependency injection or app state
_state_store = StateStore()
_narrative_engine = NarrativeEvolutionEngine(_state_store)
_narrative_engine.register_plugin(RelationshipPlugin())

@router.delete("/{novel_name}/{file_hash}/relationship", status_code=204)
def delete_relationship_cache(
    novel_name: str, 
    file_hash: str, 
    source: str, 
    target: str, 
    session: Session = Depends(get_session)
):
    """
    Delete cached relationship analysis for a specific pair.
    """
    # 5. Normalize Names - using the same logic as get_relationship_timeline
    # We must explicitly load aliases from project root because EntityAggregator() 
    # without args might not find the file if cwd is different (though usually it is project root).
    # But let's be safe and use the same logic as jobs.py or rely on default if cwd is correct.
    # Given server runs from root, default should work.
    
    # Actually, we should check if we need to load aliases.
    # Let's try to load it explicitly to be safe.
    import os
    base_dir = os.getcwd()
    alias_path = os.path.join(base_dir, "config", "aliases.json")
    
    # Check if file exists, otherwise use default
    if os.path.exists(alias_path):
        aggregator = EntityAggregator(alias_file=alias_path)
    else:
        aggregator = EntityAggregator()

    norm_source = aggregator._normalize_text(source)
    norm_target = aggregator._normalize_text(target)
    
    if not norm_source or not norm_target:
        raise HTTPException(status_code=400, detail="Invalid source or target entities")
    
    pair_id = "_".join(sorted([norm_source, norm_target]))
    
    # Delegate to StateStore
    success = _state_store.delete_history(file_hash, "relationship", pair_id)
    
    if not success:
        pass
        
    return None

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
    
    # Load aliases explicitly to match job runner logic
    import os
    base_dir = os.getcwd()
    alias_path = os.path.join(base_dir, "config", "aliases.json")
    if os.path.exists(alias_path):
        aggregator = EntityAggregator(alias_file=alias_path)
    else:
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
                    source=rel.source,
                    target=rel.target,
                    direction="forward", 
                    relation=rel.relation,
                    description=rel.description,
                    confidence=rel.confidence
                ))
            
            # Direction 2: B -> A
            elif r_source == norm_target and r_target == norm_source:
                interactions.append(RelationshipInteraction(
                    source=rel.source,
                    target=rel.target,
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
        
        # Determine if this is a state update event
        is_state_update = current_state and current_state.chapter_index == chapter.chapter_index

        # Filter: Only show chapters with actual interactions or significant state changes.
        if interactions or is_state_update:
            # If we are outputting an event, include the current state if available (context)
            if current_state:
                 # We dump the state to dict
                 # Use model_dump(mode='json') to ensure everything is JSON serializable
                 narrative_state_dict = current_state.model_dump(mode='json')

            # Construct RelationshipTimelineEvent
            # Ensure interactions list is not None (schema default is [])
            event = RelationshipTimelineEvent(
                chapter_id=str(chapter.id),
                chapter_index=chapter.chapter_index,
                chapter_title=chapter.title,
                interactions=interactions or [],
                narrative_state=narrative_state_dict
            )
            timeline_events.append(event)
            
    return timeline_events
