from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class TextSpan(BaseModel):
    """表示文本中的一个片段及其位置"""
    text: str = Field(..., description="片段内容")
    start_index: int = Field(..., description="在原文中的起始字符偏移量")
    end_index: int = Field(..., description="在原文中的结束字符偏移量")

class Chapter(BaseModel):
    """章节数据模型"""
    id: str = Field(..., description="唯一标识符 (如 'vol1_ch1')")
    title: str = Field(..., description="章节标题 (如 '第一章 序幕')")
    volume_title: Optional[str] = Field(None, description="所属分卷标题 (可选)")
    content: str = Field(..., description="章节完整文本")
    word_count: int = Field(..., description="字数")

class BookStructure(BaseModel):
    """整书结构模型"""
    book_name: str = Field(..., description="书名")
    chapters: List[Chapter] = Field(default_factory=list, description="章节列表")
    metadata: Dict = Field(default_factory=dict, description="额外元数据")

class SummarySentence(BaseModel):
    """单句总结及其溯源"""
    summary_text: str = Field(..., description="总结的句子 (LLM 生成)")
    source_spans: List[TextSpan] = Field(default_factory=list, description="对应的原文片段 (用于点击跳转)")
    confidence: Optional[float] = Field(None, description="置信度 (可选)")

class Entity(BaseModel):
    """实体模型 (世界观构建)"""
    name: str = Field(..., description="实体名称 (如 '孙杰克', '玄天宗')")
    type: str = Field(..., description="实体类型: Person(人物), Location(地点/自然环境), Organization(组织/社会环境), Item(物品), Concept(概念)")
    description: str = Field(..., description="本章中的相关描述或状态更新")
    confidence: Optional[float] = Field(None, description="置信度")

class Relationship(BaseModel):
    """实体关系模型 (v6.0)"""
    source: str = Field(..., description="主体 (Subject)，如 '孙杰克'")
    target: str = Field(..., description="客体 (Object)，如 '塔派'")
    relation: str = Field(..., description="关系类型/谓语，如 '朋友', '敌人', '攻击', '遇见'")
    description: str = Field(..., description="关系描述，如 '在垃圾场捡到的机器人'")
    confidence: float = Field(default=1.0)

class ChapterSummary(BaseModel):
    """单章总结"""
    chapter_id: str = Field(..., description="关联的章节 ID")
    chapter_title: Optional[str] = Field(None, description="章节标题")
    headline: Optional[str] = Field(None, description="一句话核心总结 (Overview Mode)")
    summary_sentences: List[SummarySentence] = Field(default_factory=list, description="总结句子列表")
    entities: List[Entity] = Field(default_factory=list, description="本章出现的关键实体及其描述")
    relationships: List[Relationship] = Field(default_factory=list, description="本章内发生的实体互动关系")
    # key_entities: List[str]  # Deprecated in v5, replaced by entities list

class AggregatedEntity(BaseModel):
    """聚合后的全局实体"""
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    description: str = Field(..., description="合并后的描述 (通常取首次出现或最详细的描述)")
    history: List[Dict] = Field(default_factory=list, description="实体描述历史: [{'chapter_id': 'ch1', 'content': '...'}, ...]")
    chapter_ids: List[str] = Field(default_factory=list, description="出现的章节ID列表")
    count: int = Field(0, description="出现次数")

class AggregatedRelationship(BaseModel):
    """聚合后的全局关系 (v6.0)"""
    source: str = Field(..., description="主体")
    target: str = Field(..., description="客体")
    # 关系是动态的，所以不应该只有一个静态的 relation 字段
    # 而是存储一个时间线列表
    timeline: List[Dict] = Field(
        default_factory=list, 
        description="关系演变历史: [{'chapter_id': 'ch1', 'relation': 'stranger', 'description': '...'}, ...]"
    )
    weight: int = Field(0, description="互动次数权重")
