from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun
from backend.schemas import NovelInfo, RunInfo
import json

router = APIRouter(prefix="/api/novels", tags=["novels"])

def get_session():
    with Session(engine) as session:
        yield session

@router.get("", response_model=List[NovelInfo])
def list_novels(session: Session = Depends(get_session)):
    novels = session.exec(select(Novel)).all()
    results = []
    for n in novels:
        hashes = [v.hash for v in n.versions]
        results.append(NovelInfo(name=n.name, hashes=hashes))
    return results

@router.get("/{novel_name}/{file_hash}/runs", response_model=List[RunInfo])
def list_runs(novel_name: str, file_hash: str, session: Session = Depends(get_session)):
    # Find version
    statement = select(NovelVersion).join(Novel).where(Novel.name == novel_name).where(NovelVersion.hash == file_hash)
    version = session.exec(statement).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Novel version not found")
    
    runs = []
    for run in version.runs:
        metadata = {}
        if run.config_snapshot:
            try:
                metadata = json.loads(run.config_snapshot)
            except:
                pass
        runs.append(RunInfo(timestamp=run.timestamp, metadata=metadata))
    
    # Sort descending
    runs.sort(key=lambda x: x.timestamp, reverse=True)
    return runs
