import time
import uuid
import threading
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel

class JobStatus(BaseModel):
    job_id: str
    type: str           # "relationship_analysis"
    status: str         # "pending", "processing", "completed", "failed"
    progress: int       # 0-100
    message: str        # "Analyzing Chapter 45/120..."
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float
    metadata: Optional[Dict[str, Any]] = None  # New field for metadata

class JobManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(JobManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.jobs: Dict[str, JobStatus] = {}
        self.active_job_id: Optional[str] = None
        self._job_lock = threading.Lock()
        self._initialized = True
        
    def submit_job(self, job_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new job and return its ID.
        Note: The actual processing must be triggered by the caller (e.g., BackgroundTasks).
        """
        job_id = str(uuid.uuid4())
        now = time.time()
        
        with self._job_lock:
            # Simple queue logic: If there is an active job, new ones are pending.
            # But here we just create the record. The worker logic decides when to run.
            # Since we use FastAPI BackgroundTasks, they run sequentially if we await? 
            # actually BackgroundTasks run in a threadpool. 
            # We want to enforce strict sequential execution for LLM tasks.
            
            job = JobStatus(
                job_id=job_id,
                type=job_type,
                status="pending",
                progress=0,
                message="Job submitted",
                created_at=now,
                updated_at=now,
                metadata=metadata
            )
            self.jobs[job_id] = job
            
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        return self.jobs.get(job_id)
        
    def list_jobs(self, active_only: bool = False):
        if active_only:
            return [j for j in self.jobs.values() if j.status in ["pending", "processing"]]
        return list(self.jobs.values())

    def update_progress(self, job_id: str, progress: int, message: str = None):
        if job_id not in self.jobs:
            return
            
        with self._job_lock:
            job = self.jobs[job_id]
            job.progress = progress
            if message:
                job.message = message
            job.updated_at = time.time()
            
            if progress >= 100:
                job.status = "completed"
            elif job.status == "pending":
                job.status = "processing"
                
    def fail_job(self, job_id: str, error_msg: str):
        if job_id not in self.jobs:
            return
            
        with self._job_lock:
            job = self.jobs[job_id]
            job.status = "failed"
            job.error = error_msg
            job.message = f"Failed: {error_msg}"
            job.updated_at = time.time()
            
    def complete_job(self, job_id: str, result: Any = None):
        if job_id not in self.jobs:
            return
            
        with self._job_lock:
            job = self.jobs[job_id]
            job.status = "completed"
            job.progress = 100
            job.message = "Analysis complete"
            job.result = result
            job.updated_at = time.time()

# Global Singleton
job_manager = JobManager()
