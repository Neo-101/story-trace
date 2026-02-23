from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from data_protocol.models import BaseEntity, BaseRelationship

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

class Entity(BaseEntity, SQLModel, table=True):
    """继承 BaseEntity: name, type, description, confidence"""
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    # BaseEntity 字段 (name, type, description, confidence) 自动包含
    count: int = 1
    
    chapter: Chapter = Relationship(back_populates="entities")

class StoryRelationship(BaseRelationship, SQLModel, table=True):
    """继承 BaseRelationship: source, target, relation, description, confidence"""
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapter.id")
    # BaseRelationship 字段自动包含
    # 注意：BaseRelationship 中是 confidence，这里之前叫 weight。
    # 为了兼容，我们可以保留 weight，或者迁移。
    # 鉴于 BaseRelationship 已经有 confidence，我们用 confidence 替代 weight 的语义（或者两者共存）
    weight: int = 1 # 互动次数，DB 特有
    
    chapter: Chapter = Relationship(back_populates="relationships")
