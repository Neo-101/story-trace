from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class NovelInfo(BaseModel):
    name: str
    hashes: List[str]

class RunInfo(BaseModel):
    timestamp: str
    file_hash: str
    metadata: Optional[Dict[str, Any]] = None

class ChapterPreview(BaseModel):
    id: str
    title: str
    headline: str
    has_summary: bool = True

class SourceSpan(BaseModel):
    start_index: int
    end_index: int
    text: str

class SummarySentence(BaseModel):
    summary_text: str
    source_spans: List[SourceSpan] = []

class EntityDetail(BaseModel):
    name: str
    type: str
    description: str
    confidence: float = 1.0

class ChapterDetail(BaseModel):
    id: str
    title: str
    headline: Optional[str] = None
    content: str
    summary_sentences: List[SummarySentence]
    entities: List[EntityDetail] = []

class TimelineEvent(BaseModel):
    chapter_id: str
    chapter_index: int
    chapter_title: str
    content: List[str]
    gap_before: int

class RelationshipInteraction(BaseModel):
    direction: str # forward or backward
    relation: str
    description: str
    confidence: float

class RelationshipTimelineEvent(BaseModel):
    chapter_id: str
    chapter_index: int
    chapter_title: str
    interactions: List[RelationshipInteraction] = []
    
    # Narrative State (Added in v4.2)
    narrative_state: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

class GraphNode(BaseModel):
    name: str
    type: str
    description: str
    count: int = 1
    chapter_ids: List[str] = []
    history: List[Dict[str, Any]] = [] # Detailed history per chapter

class EdgeEvent(BaseModel):
    chapter_id: str
    weight: int = 1
    relation: Optional[str] = None
    description: Optional[str] = None
    order: int = 0

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: int
    timeline: List[EdgeEvent] = []

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
