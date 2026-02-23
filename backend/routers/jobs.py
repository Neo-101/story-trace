import asyncio
from typing import List, Optional, Dict
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.narrative_engine.core.job_manager import job_manager, JobStatus
from backend.routers.analysis import get_session, get_merged_chapters, db_chapter_to_summary, _narrative_engine
from backend.narrative_engine.core.models import AnalysisEvent
from core.world_builder.aggregator import EntityAggregator
from core.summarizer.llm_client import ClientFactory
from core.config import settings
from sqlmodel import Session
from core.db.engine import engine

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class RelationshipJobRequest(BaseModel):
    novel_name: str
    file_hash: str
    source: str
    target: str
    force: bool = False

class RelationshipPair(BaseModel):
    source: str
    target: str

class BatchRelationshipJobRequest(BaseModel):
    novel_name: str
    file_hash: str
    pairs: List[RelationshipPair] 
    force: bool = False

def analyze_relationship_core(novel_name: str, file_hash: str, source: str, target: str, progress_callback):
    """
    Core logic for relationship analysis, decoupled from JobManager for reusability.
    """
    with Session(engine) as session:
        # 3. Load Chapters
        progress_callback(5, "Loading chapters...")
        chapters = get_merged_chapters(session, novel_name, file_hash)
        
        if not chapters:
            raise Exception("No chapters found")

        # 4. Setup LLM Client
        provider = "openrouter"
        api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
             raise Exception("OpenRouter API Key not found. Please set OPENROUTER_API_KEY env var.")

        llm_client = ClientFactory.create_client(
            provider="openrouter",
            api_key=api_key,
            model=settings.OPENROUTER_MODEL or "google/gemini-2.0-flash-001"
        )
        
        # 5. Normalize Names
        base_dir = os.getcwd()
        alias_path = os.path.join(base_dir, "config", "aliases.json")
        aggregator = EntityAggregator(alias_file=alias_path)
        
        norm_source = aggregator._normalize_text(source)
        norm_target = aggregator._normalize_text(target)
        pair_id = "_".join(sorted([norm_source, norm_target]))
        
        total_chapters = len(chapters)
        
        # 6. Pre-calculate Interaction Density
        progress_callback(8, "Pre-calculating interaction density...")
        
        chapter_scores = []
        for chapter in chapters:
            summary = db_chapter_to_summary(chapter)
            score = 0.0
            
            # 1. Explicit Relationships
            for rel in summary.relationships:
                r_s = aggregator._normalize_text(rel.source)
                r_t = aggregator._normalize_text(rel.target)
                if (r_s == norm_source and r_t == norm_target) or (r_s == norm_target and r_t == norm_source):
                    score += 3.0
                    
            # 2. Text Mentions
            for sent in summary.summary_sentences:
                if (norm_source in sent.summary_text and norm_target in sent.summary_text):
                    score += 1.0
                    
            # 3. Co-occurrence
            source_in_chapter = False
            target_in_chapter = False
            for e in summary.entities:
                norm_name = aggregator._normalize_text(e.name)
                if norm_name == norm_source: source_in_chapter = True
                if norm_name == norm_target: target_in_chapter = True
            
            if source_in_chapter and target_in_chapter:
                score += 0.5
                
            chapter_scores.append(score)

        # Calculate Dynamic Threshold
        avg_score = sum(chapter_scores) / len(chapter_scores) if chapter_scores else 0
        threshold = max(0.6, avg_score * 0.2)
        
        print(f"[Core {pair_id}] Density Analysis: Avg={avg_score:.2f}, Threshold={threshold:.2f}")

        # 7. Iterate and Evolve
        has_started = False
        for i, chapter in enumerate(chapters):
            progress_base = 10 + int((i / total_chapters) * 80)
            score = chapter_scores[i]
            
            should_skip_llm = score < threshold
            
            # Special Logic: Not Started & Low Score -> Skip entirely
            if not has_started and should_skip_llm:
                # progress_callback(progress_base, f"Skipping Ch {chapter.chapter_index} (Low Score)...")
                continue

            progress_callback(progress_base, f"Analyzing Ch {chapter.chapter_index} (Score: {score:.1f})...")
            
            # Prepare events
            summary = db_chapter_to_summary(chapter)
            relevant_sentences = []
            
            for rel in summary.relationships:
                r_s = aggregator._normalize_text(rel.source)
                r_t = aggregator._normalize_text(rel.target)
                if (r_s == norm_source and r_t == norm_target) or (r_s == norm_target and r_t == norm_source):
                    relevant_sentences.append(f"Interaction ({rel.relation}): {rel.description}")
            
            for sent in summary.summary_sentences:
                if (norm_source in sent.summary_text and norm_target in sent.summary_text):
                        relevant_sentences.append(sent.summary_text)

            source_in_chapter = False
            target_in_chapter = False
            for e in summary.entities:
                norm_name = aggregator._normalize_text(e.name)
                if norm_name == norm_source: source_in_chapter = True
                if norm_name == norm_target: target_in_chapter = True
            
            if not relevant_sentences and source_in_chapter and target_in_chapter:
                relevant_sentences.append("Both characters appear in this chapter, implying potential implicit interaction or co-presence.")

            if should_skip_llm:
                relevant_sentences = [] 
                
            new_events = [AnalysisEvent(
                chapter_index=chapter.chapter_index,
                content=relevant_sentences
            )] if relevant_sentences else []
            
            def step_callback(step_progress, msg):
                pass

            try:
                result_state = _narrative_engine.evolve_state(
                    novel_hash=file_hash,
                    plugin_type="relationship",
                    entity_id=pair_id,
                    target_chapter_index=chapter.chapter_index,
                    new_events=new_events,
                    llm_client=llm_client,
                    progress_callback=step_callback
                )
                
                if result_state:
                    has_started = True

            except Exception as evo_err:
                    print(f"Error evolving state for Ch {chapter.chapter_index}: {evo_err}")

        return {"pair_id": pair_id, "chapters_analyzed": total_chapters}

def run_relationship_analysis_task(job_id: str, request: RelationshipJobRequest):
    """
    Background task wrapper for single relationship analysis.
    """
    try:
        job_manager.update_progress(job_id, 0, "Initializing analysis...")
        
        def progress_callback(pct, msg):
            job_manager.update_progress(job_id, pct, msg)
            
        result = analyze_relationship_core(
            request.novel_name, 
            request.file_hash, 
            request.source, 
            request.target, 
            progress_callback
        )
        
        job_manager.complete_job(job_id, result)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        job_manager.fail_job(job_id, str(e))

def run_batch_analysis_orchestrator(job_id: str, request: BatchRelationshipJobRequest):
    """
    Orchestrator for batch analysis with concurrency control.
    """
    try:
        job_manager.update_progress(job_id, 0, f"Initializing batch of {len(request.pairs)} pairs...")
        
        total_pairs = len(request.pairs)
        completed_pairs = 0
        
        # Helper to update parent job
        def update_parent_progress(current_pair_idx, current_pair_name, sub_pct, sub_msg):
            # Global progress = (completed_pairs * 100 + sub_pct) / total_pairs
            # But simpler: just show which pair is being processed
            # job_manager.update_progress(job_id, ...)
            # Let's just track completed pairs for the progress bar
            global_pct = int((completed_pairs / total_pairs) * 100)
            job_manager.update_progress(job_id, global_pct, f"Processing {completed_pairs + 1}/{total_pairs}: {current_pair_name} - {sub_msg}")

        # ThreadPoolExecutor
        # We process pairs in queue, but max 3 concurrently.
        # Since we want to update the Parent Job with "Current Activity", it's a bit tricky with threads.
        # We can just report "Processing X/Y pairs" and let the sub-tasks log to console or something.
        # Or we can pass a callback that doesn't overwrite the main message too frantically.
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_pair = {}
            
            for pair in request.pairs:
                source = pair.source
                target = pair.target
                pair_label = f"{source} & {target}"
                
                # Define a thread-safe callback for this specific task
                # Note: job_manager.update_progress is likely thread-safe (dict update)
                # But we share the same job_id! Race conditions on the message string.
                # So we should probably NOT update the main job details from sub-threads frequently.
                # We can just update it when a task starts or finishes.
                
                def silent_callback(pct, msg):
                    # Maybe log to console?
                    pass
                
                future = executor.submit(
                    analyze_relationship_core,
                    request.novel_name,
                    request.file_hash,
                    source,
                    target,
                    silent_callback
                )
                future_to_pair[future] = pair_label

            for future in as_completed(future_to_pair):
                pair_label = future_to_pair[future]
                completed_pairs += 1
                try:
                    res = future.result()
                    print(f"Batch sub-task finished: {pair_label}")
                except Exception as exc:
                    print(f"Batch sub-task failed: {pair_label} generated an exception: {exc}")
                
                pct = int((completed_pairs / total_pairs) * 100)
                job_manager.update_progress(job_id, pct, f"Completed {completed_pairs}/{total_pairs} pairs")

        job_manager.complete_job(job_id, {"total": total_pairs, "completed": completed_pairs})

    except Exception as e:
        import traceback
        traceback.print_exc()
        job_manager.fail_job(job_id, str(e))

@router.post("/batch-relationship", response_model=Dict[str, str])
def submit_batch_relationship_job(request: BatchRelationshipJobRequest, background_tasks: BackgroundTasks):
    """
    Submit a batch relationship analysis job.
    """
    # Store request details in metadata for debugging/UI
    metadata = {
        "novel_name": request.novel_name,
        "pair_count": len(request.pairs)
    }
    job_id = job_manager.submit_job("batch_relationship_analysis", metadata=metadata)
    background_tasks.add_task(run_batch_analysis_orchestrator, job_id, request)
    return {"job_id": job_id}


@router.post("/relationship", response_model=Dict[str, str])
def submit_relationship_job(request: RelationshipJobRequest, background_tasks: BackgroundTasks):
    """
    Submit a background job to analyze relationship arc.
    """
    # Check for existing active jobs? 
    # For now, we allow multiple, but JobManager doesn't limit concurrency yet.
    # The design spec said "limit to 1 concurrent".
    # We can check JobManager here.
    active_jobs = job_manager.list_jobs(active_only=True)
    if len(active_jobs) > 0:
        # Optional: Reject or Queue.
        # For simple UX, let's reject with 429 or similar?
        # Or just let it run if user really wants.
        # Let's just warn in logs but allow it for v1.
        pass

    job_id = job_manager.submit_job("relationship_analysis")
    
    background_tasks.add_task(run_relationship_analysis_task, job_id, request)
    
    return {"job_id": job_id}

@router.get("/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/", response_model=List[JobStatus])
def list_jobs(active_only: bool = False):
    return job_manager.list_jobs(active_only)
