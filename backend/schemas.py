from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from data_protocol.models import BaseEntity, BaseRelationship, SummarySentence, TextSpan as SourceSpan

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

class EntityDetail(BaseEntity):
    """继承 BaseEntity"""
    pass

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

class RelationshipInteraction(BaseRelationship):
    """继承 BaseRelationship"""
    direction: str = "forward" # forward or backward

class RelationshipTimelineEvent(BaseModel):
    chapter_id: str
    chapter_index: int
    chapter_title: str
    interactions: List[RelationshipInteraction] = []
    
    # Narrative State (Added in v4.2)
    narrative_state: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

class GraphNode(BaseEntity):
    """继承 BaseEntity，用于图谱节点"""
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
