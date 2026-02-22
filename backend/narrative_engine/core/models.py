from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class BaseNarrativeState(BaseModel):
    """
    Abstract base state for all narrative entities (Characters, Locations, Items, Factions).
    Represents the state of an entity at a specific point in the narrative timeline.
    """
    # Meta
    entity_id: str = Field(..., description="Unique identifier for the entity or pair (e.g., 'LiXiaoyao_LinYueru')")
    chapter_index: int = Field(..., description="The end chapter index of this state block")
    version: str = Field("1.0", description="Schema version")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Narrative Content
    summary_so_far: str = Field(..., description="LLM-generated summary of the entity's history up to this point")
    key_tags: List[str] = Field(default_factory=list, description="High-level tags (e.g., 'Rival', 'Cursed', 'Lost')")
    
    # Context for Next Analysis
    unresolved_threads: List[str] = Field(default_factory=list, description="Issues/Questions carried over to next block")

    class Config:
        extra = "allow" # Allow plugins to add custom fields if needed dynamically

class RelationshipState(BaseNarrativeState):
    """
    Specific state for a relationship between two characters.
    """
    source: str = Field(..., description="Entity A Name")
    target: str = Field(..., description="Entity B Name")
    
    # Quantitative Metrics (0-100)
    trust_level: int = Field(50, ge=0, le=100, description="Trust level (0=Betrayal, 100=Blind Faith)")
    romance_level: int = Field(0, ge=0, le=100, description="Romance level (0=Platonic, 100=Soulmates)")
    conflict_level: int = Field(0, ge=0, le=100, description="Conflict level (0=Peace, 100=War)")
    
    # Qualitative Analysis
    dominant_archetype: str = Field("Stranger", description="Primary relationship archetype (e.g., 'Enemies to Lovers')")
    current_stage: str = Field("Initial", description="Current stage description (e.g., 'The Misunderstanding')")
    
    @property
    def pair_id(self) -> str:
        """Helper to generate consistent ID for undirected pairs (lexicographically sorted)"""
        return "_".join(sorted([self.source, self.target]))

class NarrativeBlock(BaseModel):
    """
    Represents a block of analysis result.
    It contains the state snapshot and the events that led to it.
    """
    range_start: int
    range_end: int
    state: Union[RelationshipState, BaseNarrativeState]
    events_digest: List[Dict[str, Any]] = Field(default_factory=list, description="Summary of key events in this block")
