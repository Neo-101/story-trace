from typing import List, Dict, Optional
from pydantic import BaseModel

class NovelInfo(BaseModel):
    name: str
    hashes: List[str]

class RunInfo(BaseModel):
    timestamp: str
    metadata: Optional[Dict]

class ChapterPreview(BaseModel):
    title: str
    file_path: str

class ChapterDetail(BaseModel):
    id: str
    title: str
    headline: str
    content: str
    summary_sentences: List[Dict]
    entities: List[Dict] = []
