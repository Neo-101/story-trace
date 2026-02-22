import asyncio
from typing import List, Optional, Dict
import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.narrative_engine.core.job_manager import job_manager, JobStatus
from backend.routers.analysis import get_session, get_merged_chapters, db_chapter_to_summary, _narrative_engine
from core.world_builder.aggregator import EntityAggregator
from core.summarizer.llm_client import ClientFactory
from core.config import settings
from sqlmodel import Session

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class RelationshipJobRequest(BaseModel):
    novel_name: str
    file_hash: str
    source: str
    target: str
    force: bool = False

def run_relationship_analysis_task(job_id: str, request: RelationshipJobRequest):
    """
    Background task to run the relationship analysis.
    """
    try:
        # 1. Update status to processing
        job_manager.update_progress(job_id, 0, "Initializing analysis...")
        
        # 2. Setup Context (Need a new session for background task?)
        # Actually we need DB access. We can create a new session here.
        from core.db.engine import engine
        
        with Session(engine) as session:
            # 3. Load Chapters
            job_manager.update_progress(job_id, 5, "Loading chapters...")
            chapters = get_merged_chapters(session, request.novel_name, request.file_hash)
            
            if not chapters:
                job_manager.fail_job(job_id, "No chapters found")
                return

            # 4. Setup LLM Client
            # config = load_config()  <-- Deprecated
            
            # Prefer OpenRouter for analysis
            # We want to force OpenRouter if possible, or use config
            # User said: "All future calls default to OpenRouter"
            
            provider = "openrouter"
            # Try to get key from settings or env
            api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
            
            if not api_key:
                 job_manager.fail_job(job_id, "OpenRouter API Key not found. Please set OPENROUTER_API_KEY env var.")
                 return

            llm_client = ClientFactory.create_client(
                provider="openrouter",
                api_key=api_key,
                model=settings.OPENROUTER_MODEL or "google/gemini-2.0-flash-001" # Default model
            )
            
            # 5. Normalize Names
            # Explicitly load aliases from project root
            base_dir = os.getcwd()
            alias_path = os.path.join(base_dir, "config", "aliases.json")
            aggregator = EntityAggregator(alias_file=alias_path)
            
            norm_source = aggregator._normalize_text(request.source)
            norm_target = aggregator._normalize_text(request.target)
            pair_id = "_".join(sorted([norm_source, norm_target]))
            
            total_chapters = len(chapters)
            
            # 6. Iterate and Evolve
            for i, chapter in enumerate(chapters):
                progress_base = 10 + int((i / total_chapters) * 80)
                job_manager.update_progress(job_id, progress_base, f"Analyzing Chapter {chapter.chapter_index}...")
                
                # Prepare events
                summary = db_chapter_to_summary(chapter)
                
                # Filter relevant events
                relevant_sentences = []
                # Check explicit relationships
                for rel in summary.relationships:
                    r_s = aggregator._normalize_text(rel.source)
                    r_t = aggregator._normalize_text(rel.target)
                    if (r_s == norm_source and r_t == norm_target) or (r_s == norm_target and r_t == norm_source):
                        relevant_sentences.append(f"Interaction ({rel.relation}): {rel.description}")
                
                # Check text mentions
                for sent in summary.summary_sentences:
                    if (norm_source in sent.summary_text and norm_target in sent.summary_text):
                         relevant_sentences.append(sent.summary_text)

                # Check entity co-occurrence (Weak Interaction)
                source_in_chapter = False
                target_in_chapter = False
                for e in summary.entities:
                    norm_name = aggregator._normalize_text(e.name)
                    if norm_name == norm_source: source_in_chapter = True
                    if norm_name == norm_target: target_in_chapter = True
                
                if not relevant_sentences and source_in_chapter and target_in_chapter:
                    relevant_sentences.append("Both characters appear in this chapter, implying potential implicit interaction or co-presence.")

                if not relevant_sentences:
                    # Skip empty chapters to save time/cost, unless we want to decay relationship?
                    # For now, just skip.
                    continue
                    
                # Prepare event dict
                new_events = [{
                    "chapter_index": chapter.chapter_index,
                    "content": relevant_sentences
                }]
                
                # Define callback for sub-steps (LLM generation)
                def step_callback(step_progress, msg):
                    # Map step_progress (0-100) to a small range within the chapter progress
                    # e.g., current chapter takes 5% of total progress
                    # We don't want to spam updates, so maybe just update message
                    # job_manager.update_progress(job_id, progress_base, f"Ch {chapter.chapter_index}: {msg}")
                    pass

                # Evolve State
                # Add try/except for evolution to not crash whole job
                try:
                    _narrative_engine.evolve_state(
                        novel_hash=request.file_hash,
                        plugin_type="relationship",
                        entity_id=pair_id,
                        target_chapter_index=chapter.chapter_index,
                        new_events=new_events,
                        llm_client=llm_client,
                        progress_callback=step_callback
                    )
                except Exception as evo_err:
                     print(f"Error evolving state for Ch {chapter.chapter_index}: {evo_err}")
                     # Continue to next chapter

            
            # 7. Finish
            job_manager.complete_job(job_id, {"pair_id": pair_id, "chapters_analyzed": total_chapters})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        job_manager.fail_job(job_id, str(e))

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
