from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from fastapi import HTTPException
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter
from data_protocol.models import (
    ChapterSummary, 
    SummarySentence as ProtoSummarySentence, 
    Entity as ProtoEntity, 
    Relationship as ProtoRelationship, 
    TextSpan as ProtoTextSpan,
    ConceptStage
)
from backend.schemas import TimelineEvent
from core.world_builder.aggregator import EntityAggregator
import json

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
        # Instead of raising HTTPException here (which couples to API), return empty or raise ValueError
        # For now, keep simple behavior or raise consistent error
        return []
    
    # 2. Get all runs sorted by timestamp (oldest first)
    runs = sorted(version.runs, key=lambda r: r.timestamp)
    
    merged_map: Dict[int, Chapter] = {}
    
    for run in runs:
        for chapter in run.chapters:
            merged_map[chapter.chapter_index] = chapter
            
    # 3. Return sorted list
    return [merged_map[idx] for idx in sorted(merged_map.keys())]

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
        # Deserialize concept_evolution
        concept_evolution = []
        if hasattr(e, 'concept_evolution_json') and e.concept_evolution_json:
             try:
                 raw_stages = json.loads(e.concept_evolution_json)
                 for stage in raw_stages:
                     if isinstance(stage, dict):
                         concept_evolution.append(ConceptStage(**stage))
             except:
                 pass
        
        entities.append(ProtoEntity(
            name=e.name,
            type=e.type,
            description=e.description or "",
            confidence=e.confidence or 1.0,
            concept_evolution=concept_evolution 
        ))

    # Convert relationships
    rels = []
    for r in db_chapter.relationships:
        rels.append(ProtoRelationship(
            source=r.source,
            target=r.target,
            relation=r.relation,
            description=r.description or "",
            confidence=r.confidence or 1.0
        ))
    
    return ChapterSummary(
        chapter_id=str(db_chapter.id),
        chapter_index=db_chapter.chapter_index,
        chapter_title=db_chapter.title,
        headline=db_chapter.headline,
        summary_sentences=summaries,
        entities=entities,
        relationships=rels
    )

def get_entity_timeline_logic(chapters: List[Chapter], entity_name: str) -> List[TimelineEvent]:
    """
    Core logic to generate entity timeline from chapters.
    """
    timeline_events = []
    
    # Try to load aliases if possible, otherwise default
    import os
    base_dir = os.getcwd()
    alias_path = os.path.join(base_dir, "config", "aliases.json")
    if os.path.exists(alias_path):
        aggregator = EntityAggregator(alias_file=alias_path)
    else:
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
                chapter_index=chapter.chapter_index,
                chapter_title=chapter.title,
                content=content if content else ["本章提及该实体。"],
                gap_before=max(0, gap)
            ))
            
            last_chapter_idx = chapter.chapter_index
            
    return timeline_events
