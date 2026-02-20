import pytest
from unittest.mock import MagicMock
from core.summarizer.generator import SummaryGenerator
from core.summarizer.llm_client import LLMClient
from data_protocol.models import Chapter, Entity

class MockLLMClient(LLMClient):
    def __init__(self, response_text):
        self.response_text = response_text
    
    def chat_completion(self, messages):
        return self.response_text

def test_generator_parses_entities():
    """测试生成器能否正确解析 entities 字段"""
    
    # 模拟 LLM 返回的 JSON
    mock_response = """
    ```json
    {
        "headline": "Test Headline",
        "summary_sentences": ["Summary 1", "Summary 2"],
        "entities": [
            {"name": "Alice", "type": "Person", "description": "Protagonist"},
            {"name": "Wonderland", "type": "Location", "description": "Magic world"}
        ]
    }
    ```
    """
    
    client = MockLLMClient(mock_response)
    generator = SummaryGenerator(client)
    
    chapter = Chapter(
        id="ch1", 
        title="Test Chapter", 
        content="Alice went to Wonderland.", 
        word_count=100
    )
    
    summary = generator.generate_summary(chapter)
    
    # 验证 Headline 和 Summaries
    assert summary.headline == "Test Headline"
    assert len(summary.summary_sentences) == 2
    
    # 验证 Entities
    assert len(summary.entities) == 2
    
    e1 = summary.entities[0]
    assert e1.name == "Alice"
    assert e1.type == "Person"
    assert e1.description == "Protagonist"
    
    e2 = summary.entities[1]
    assert e2.name == "Wonderland"
    assert e2.type == "Location"
    assert e2.description == "Magic world"

def test_generator_handles_missing_entities():
    """测试当 LLM 未返回 entities 时，字段应为空列表"""
    
    mock_response = """
    {
        "headline": "No Entities",
        "summary_sentences": ["Just summary"]
    }
    """
    
    client = MockLLMClient(mock_response)
    generator = SummaryGenerator(client)
    
    chapter = Chapter(id="ch2", title="No Entities", content="...", word_count=10)
    summary = generator.generate_summary(chapter)
    
    assert summary.entities == []

def test_generator_handles_malformed_entity():
    """测试部分实体数据格式错误时，不应导致崩溃"""
    
    mock_response = """
    {
        "headline": "Bad Entity",
        "summary_sentences": [],
        "entities": [
            {"name": "Valid", "type": "Person", "description": "OK"},
            {"wrong_field": "Invalid"} 
        ]
    }
    """
    # 第二个实体缺少 name/type/description，Pydantic 验证可能会失败，
    # generator 应该捕获异常并跳过该实体，或者由 Pydantic 抛出错误（取决于实现）
    # 在当前的 generator 实现中，使用了 .get() 并提供了默认值，所以应该能通过，或者被 try-except 捕获
    
    client = MockLLMClient(mock_response)
    generator = SummaryGenerator(client)
    
    chapter = Chapter(id="ch3", title="Bad Entity", content="...", word_count=10)
    summary = generator.generate_summary(chapter)
    
    # 应该至少有一个有效的实体，或者两个（如果 generator 做了容错处理）
    # 当前代码: name=ent.get("name", "Unknown"), 所以第二个实体会变成 "Unknown"
    assert len(summary.entities) == 2
    assert summary.entities[0].name == "Valid"
    assert summary.entities[1].name == "Unknown"
