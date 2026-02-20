import pytest
from data_protocol.models import ChapterSummary, SummarySentence, Entity
from core.summarizer.prompts import Prompts

def test_entity_model_initialization():
    """测试 Entity 模型的初始化"""
    entity = Entity(
        name="孙杰克",
        type="Person",
        description="失忆的主角",
        confidence=0.9
    )
    assert entity.name == "孙杰克"
    assert entity.type == "Person"
    assert entity.description == "失忆的主角"
    assert entity.confidence == 0.9

def test_chapter_summary_with_entities():
    """测试 ChapterSummary 包含 entities 字段"""
    summary = ChapterSummary(
        chapter_id="ch1",
        chapter_title="Chapter 1",
        headline="Headline",
        summary_sentences=[
            SummarySentence(summary_text="Sentence 1", source_spans=[])
        ],
        entities=[
            Entity(name="E1", type="Person", description="D1"),
            Entity(name="E2", type="Item", description="D2")
        ]
    )
    
    assert len(summary.entities) == 2
    assert summary.entities[0].name == "E1"
    assert summary.entities[1].type == "Item"

def test_prompt_includes_entity_instructions():
    """测试 Prompt 中是否包含关于实体的指令"""
    system_prompt = Prompts.SYSTEM_PROMPT
    assert "提取本章出现的关键实体" in system_prompt
    assert "包括人物(Person)" in system_prompt
    assert "entities" in system_prompt
    
    user_prompt = Prompts.USER_PROMPT_TEMPLATE
    assert "entities" in user_prompt
    assert "type" in user_prompt
