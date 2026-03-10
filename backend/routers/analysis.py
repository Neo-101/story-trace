from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Summary, Entity, StoryRelationship
from backend.schemas import (
    ChapterPreview, ChapterDetail, EntityDetail, SummarySentence, SourceSpan,
    GraphData, GraphNode, GraphEdge, EdgeEvent, TimelineEvent, RelationshipTimelineEvent,
    GroupSummaryResponse, GroupSummaryRequest,
    RelationshipInteraction, ConceptAnalysisRequest,
    RelationshipStageRequest, RelationshipStageResponse, RelationshipStageLabel
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
            index=c.chapter_index,
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
        index=chapter.chapter_index,
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

@router.post("/{novel_name}/{file_hash}/analyze/group-summary", response_model=GroupSummaryResponse)
def analyze_group_summary(
    novel_name: str,
    file_hash: str,
    request: GroupSummaryRequest,
    session: Session = Depends(get_session)
):
    """
    On-demand analysis for a range of chapters for a specific entity.
    Uses LLM to summarize the entity's arc in these chapters.
    """
    from core.db.models import EntityGroupSummary
    from datetime import datetime
    
    # 1. Check Cache
    if not request.force:
        cached = session.exec(select(EntityGroupSummary).where(
            EntityGroupSummary.novel_name == novel_name,
            EntityGroupSummary.file_hash == file_hash,
            EntityGroupSummary.entity_name == request.entity_name,
            EntityGroupSummary.chapter_start == request.chapter_start,
            EntityGroupSummary.chapter_end == request.chapter_end
        )).first()
        
        # Check if cache is valid (covers the same number of chapters)
        # Note: request.chapter_end - request.chapter_start + 1 is the theoretical range,
        # but actual chapters might be sparse. We should ideally check event count.
        # But here we only have the request range.
        # Let's assume if the range matches, it's the same "Group".
        # But if we added new chapters, they might fall into this range?
        # No, chapter indices are stable.
        # The issue is if we ingested Chapter 201, and previous run only had 200.
        # Then the "Group 200-209" previously only covered 1 chapter. Now it covers 2.
        
        # We need to know how many actual chapters are in this range NOW.
        chapters = get_merged_chapters(session, novel_name, file_hash)
        target_chapters = [c for c in chapters if request.chapter_start <= c.chapter_index <= request.chapter_end]
        current_count = len(target_chapters)
        
        if cached:
            # If cached count matches current count, it's valid.
            # If cached.chapter_count is 0 (old schema), we force update (or accept it once).
            # Let's be strict: if count mismatch, invalidate.
            if cached.chapter_count == current_count:
                return GroupSummaryResponse(summary=cached.summary_text, is_cached=True)
            else:
                # Invalidate cache (delete it)
                session.delete(cached)
                session.commit()
    else:
        # Fetch chapters if force is true (we skipped it in if block)
        chapters = get_merged_chapters(session, novel_name, file_hash)
        target_chapters = [c for c in chapters if request.chapter_start <= c.chapter_index <= request.chapter_end]
        current_count = len(target_chapters)

    # 2. Fetch Timeline Events (target_chapters already fetched)
    
    if not target_chapters:
         return GroupSummaryResponse(summary="No events in this range.", is_cached=False)
         
    timeline_events = get_entity_timeline_logic(target_chapters, request.entity_name)
    
    if not timeline_events:
         return GroupSummaryResponse(summary="No events in this range.", is_cached=False)
         
    # 3. Construct Prompt
    # Simplify timeline for prompt
    context_lines = []
    for event in timeline_events:
        # Use content (relevant entity sentences) if available, otherwise fallback to headline.
        # This ensures the summary is entity-centric.
        relevant_text = " ".join(event.content) if event.content else event.headline
        context_lines.append(f"Chapter {event.chapter_index}: {relevant_text}")
        
    context_text = "\n".join(context_lines)
    
    prompt = f"""
    Please summarize the development of the entity "{request.entity_name}" in the following chapter range (Ch {request.chapter_start}-{request.chapter_end}).
    Keep it concise (1 sentence, max 50 words). Focus on key actions or status changes.
    Answer in Chinese (Simplified).
    
    Context:
    {context_text}
    
    Summary:
    """
    
    # 4. Call LLM
    try:
        # Initialize Client (Reuse logic from analyze_concept or make a helper)
        if settings.OPENROUTER_API_KEY:
             llm_client = ClientFactory.create_client(
                 provider="openrouter",
                 api_key=settings.OPENROUTER_API_KEY,
                 model=settings.OPENROUTER_MODEL
             )
        else:
             llm_client = ClientFactory.create_client(
                 provider="local",
                 base_url=settings.LOCAL_LLM_BASE_URL,
                 model=settings.LOCAL_LLM_MODEL
             )
             
        response = llm_client.generate(prompt)
        summary_text = response.strip().strip('"')
        
        # 5. Save Cache
        # Delete old if force (already done if cached existed and mismatched)
        if request.force:
             session.exec(select(EntityGroupSummary).where(
                EntityGroupSummary.novel_name == novel_name,
                EntityGroupSummary.file_hash == file_hash,
                EntityGroupSummary.entity_name == request.entity_name,
                EntityGroupSummary.chapter_start == request.chapter_start,
                EntityGroupSummary.chapter_end == request.chapter_end
            )).delete() # This might need session.delete(obj) iteration for sqlmodel
        
        # Just add new (or replace)
        new_summary = EntityGroupSummary(
            novel_name=novel_name,
            file_hash=file_hash,
            entity_name=request.entity_name,
            chapter_start=request.chapter_start,
            chapter_end=request.chapter_end,
            summary_text=summary_text,
            chapter_count=current_count, # Save current count
            timestamp=datetime.now().isoformat()
        )
        session.add(new_summary)
        session.commit()
        
        return GroupSummaryResponse(summary=summary_text, is_cached=False)
        
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback to simple concatenation
        start = timeline_events[0].headline or "Start"
        end = timeline_events[-1].headline or "End"
        return GroupSummaryResponse(summary=f"{start} ... {end} (Auto-generated)", is_cached=False)

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

@router.post("/{novel_name}/{file_hash}/analyze/relationship-stage", response_model=RelationshipStageResponse)
def analyze_relationship_stage(
    novel_name: str,
    file_hash: str,
    request: RelationshipStageRequest,
    session: Session = Depends(get_session)
):
    """
    On-demand analysis for a relationship stage between two entities in a chapter range.
    """
    from core.db.models import RelationshipStage
    from backend.narrative_engine.prompts import RELATIONSHIP_STAGE_TEMPLATE
    from datetime import datetime
    import os

    # 0. Normalize Entity Names
    base_dir = os.getcwd()
    alias_path = os.path.join(base_dir, "config", "aliases.json")
    if os.path.exists(alias_path):
        aggregator = EntityAggregator(alias_file=alias_path)
    else:
        aggregator = EntityAggregator()

    norm_source = aggregator._normalize_text(request.source_entity)
    norm_target = aggregator._normalize_text(request.target_entity)
    
    if not norm_source or not norm_target:
        raise HTTPException(status_code=400, detail="Invalid source or target entities")

    # 1. Check Cache
    if not request.force:
        cached = session.exec(select(RelationshipStage).where(
            RelationshipStage.novel_name == novel_name,
            RelationshipStage.file_hash == file_hash,
            RelationshipStage.source_entity == norm_source,
            RelationshipStage.target_entity == norm_target,
            RelationshipStage.start_chapter == request.chapter_start,
            RelationshipStage.end_chapter == request.chapter_end
        )).first()
        
        if cached:
                # We can also check event_count consistency if we want to be strict
                return RelationshipStageResponse(
                    start_chapter=cached.start_chapter,
                    end_chapter=cached.end_chapter,
                    stage_label=cached.stage_label,
                    summary_text=cached.summary_text,
                    sentiment_score=cached.sentiment_score,
                    is_cached=True
                )

    # 2. Fetch Interactions
    chapters = get_merged_chapters(session, novel_name, file_hash)
    target_chapters = [c for c in chapters if request.chapter_start <= c.chapter_index <= request.chapter_end]
    
    if not target_chapters:
         return RelationshipStageResponse(
             start_chapter=request.chapter_start,
             end_chapter=request.chapter_end,
             stage_label="Unknown",
             summary_text="No chapters found in this range.",
             sentiment_score=0.0,
             is_cached=False
         )

    interactions = []
    for chapter in target_chapters:
        summary = db_chapter_to_summary(chapter)
        for rel in summary.relationships:
            r_source = aggregator._normalize_text(rel.source)
            r_target = aggregator._normalize_text(rel.target)
            
            # Check if this relationship involves our pair
            if (r_source == norm_source and r_target == norm_target) or \
               (r_source == norm_target and r_target == norm_source):
                
                interactions.append({
                    "chapter": chapter.chapter_index,
                    "source": rel.source, # Original name for context
                    "target": rel.target,
                    "relation": rel.relation,
                    "description": rel.description
                })

    current_event_count = len(interactions)

    if not interactions:
        return RelationshipStageResponse(
             start_chapter=request.chapter_start,
             end_chapter=request.chapter_end,
             stage_label="No Interaction",
             summary_text="No interactions found in this range.",
             sentiment_score=0.0,
             is_cached=False
         )

    # 3. Construct Prompt
    interactions_text = ""
    for item in interactions:
        interactions_text += f"- Ch {item['chapter']}: {item['source']} -> {item['target']} ({item['relation']}): {item['description']}\n"

    prompt = RELATIONSHIP_STAGE_TEMPLATE.format(
        source=norm_source,
        target=norm_target,
        start_chapter=request.chapter_start,
        end_chapter=request.chapter_end,
        interactions_text=interactions_text
    )

    # 4. Call LLM
    try:
        if settings.OPENROUTER_API_KEY:
             llm_client = ClientFactory.create_client(
                 provider="openrouter",
                 api_key=settings.OPENROUTER_API_KEY,
                 model=settings.OPENROUTER_MODEL
             )
        else:
             llm_client = ClientFactory.create_client(
                 provider="local",
                 base_url=settings.LOCAL_LLM_BASE_URL,
                 model=settings.LOCAL_LLM_MODEL
             )
             
        response = llm_client.generate(prompt)
        
        # Parse JSON
        # Robust parsing: try to find the JSON block
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                data = json.loads(json_str)
            else:
                data = json.loads(response) # Try direct parse
        except json.JSONDecodeError:
            print(f"LLM JSON Error: {response}")
            # Fallback
            data = {
                "stage_label": "Analysis Failed",
                "summary_text": response[:100] + "...",
                "sentiment_score": 0.0
            }

        stage_label = data.get("stage_label", "Unknown")
        summary_text = data.get("summary_text", "No summary generated.")
        sentiment_score = float(data.get("sentiment_score", 0.0))

        # 5. Save Cache
        # Delete old if exists (force mode)
        if request.force:
             existing = session.exec(select(RelationshipStage).where(
                RelationshipStage.novel_name == novel_name,
                RelationshipStage.file_hash == file_hash,
                RelationshipStage.source_entity == norm_source,
                RelationshipStage.target_entity == norm_target,
                RelationshipStage.start_chapter == request.chapter_start,
                RelationshipStage.end_chapter == request.chapter_end
            )).all()
             for item in existing:
                session.delete(item)
        
        new_stage = RelationshipStage(
            novel_name=novel_name,
            file_hash=file_hash,
            source_entity=norm_source,
            target_entity=norm_target,
            start_chapter=request.chapter_start,
            end_chapter=request.chapter_end,
            stage_label=stage_label,
            summary_text=summary_text,
            sentiment_score=sentiment_score,
            event_count=current_event_count,
            timestamp=datetime.now().isoformat()
        )
        session.add(new_stage)
        session.commit()
        
        return RelationshipStageResponse(
            start_chapter=request.chapter_start,
            end_chapter=request.chapter_end,
            stage_label=stage_label,
            summary_text=summary_text,
            sentiment_score=sentiment_score,
            is_cached=False
        )

    except Exception as e:
        print(f"LLM/Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{novel_name}/{file_hash}/relationship/stages", response_model=List[RelationshipStageResponse])
def get_relationship_stages(
    novel_name: str, 
    file_hash: str, 
    source: str, 
    target: str, 
    session: Session = Depends(get_session)
):
    """
    Get all analyzed relationship stages for a specific pair.
    """
    from core.db.models import RelationshipStage
    import os

    # Normalize Names
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

    stages = session.exec(select(RelationshipStage).where(
        RelationshipStage.novel_name == novel_name,
        RelationshipStage.file_hash == file_hash,
        RelationshipStage.source_entity == norm_source,
        RelationshipStage.target_entity == norm_target
    ).order_by(RelationshipStage.start_chapter)).all()
    
    return [
        RelationshipStageResponse(
            start_chapter=s.start_chapter,
            end_chapter=s.end_chapter,
            stage_label=s.stage_label,
            summary_text=s.summary_text,
            sentiment_score=s.sentiment_score,
            is_cached=True
        )
        for s in stages
    ]

@router.get("/{novel_name}/{file_hash}/relationship/all_stages", response_model=List[RelationshipStageLabel])
def get_all_relationship_stages(
    novel_name: str, 
    file_hash: str, 
    session: Session = Depends(get_session)
):
    """
    Get index of all relationship stages for the novel (lightweight).
    Used for graph visualization to show labels.
    """
    from core.db.models import RelationshipStage
    stages = session.exec(select(RelationshipStage).where(
        RelationshipStage.novel_name == novel_name,
        RelationshipStage.file_hash == file_hash
    )).all()
    
    return [
        RelationshipStageLabel(
            source_entity=s.source_entity,
            target_entity=s.target_entity,
            start_chapter=s.start_chapter,
            end_chapter=s.end_chapter,
            stage_label=s.stage_label
        )
        for s in stages
    ]

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
