from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class Novel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    
    versions: List["NovelVersion"] = Relationship(back_populates="novel")

class NovelVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    novel_id: int = Field(foreign_key="novel.id")
    hash: str = Field(index=True)
    
    novel: Novel = Relationship(back_populates="versions")
    runs: List["AnalysisRun"] = Relationship(back_populates="version")

class AnalysisRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    version_id: int = Field(foreign_key="novelversion.id")
    timestamp: str = Field(index=True)
    config_snapshot: Optional[str] = None
    
    version: NovelVersion = Relationship(back_populates="runs")
    chapters: List["Chapter"] = Relationship(back_populates="run")

class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="analysisrun.id")
    chapter_index: int
    title: str
    headline: Optional[str] = None
    content: Optional[str] = None
    
    run: AnalysisRun = Relationship(back_populates="chapters")
    summaries: List["Summary"] = Relationship(back_populates="chapter")
    entities: List["Entity"] = Relationship(back_populates="chapter")
    relationships: List["StoryRelationship"] = Relationship(back_populates="chapter")

class Summary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    text: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    
    chapter: Chapter = Relationship(back_populates="summaries")

class Entity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    name: str
    type: str
    description: Optional[str] = None
    count: int = 1
    
    chapter: Chapter = Relationship(back_populates="entities")

class StoryRelationship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    source: str
    target: str
    relation: str
    description: Optional[str] = None
    weight: int = 1
    
    chapter: Chapter = Relationship(back_populates="relationships")
