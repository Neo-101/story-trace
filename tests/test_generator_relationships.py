import json
from unittest.mock import Mock
import json
from core.summarizer.generator import SummaryGenerator
from data_protocol.models import Chapter

class TestGeneratorRelationships:
    def test_parse_relationships(self):
        # Mock LLM Client
        mock_llm = Mock()
        # Ensure json string is valid and includes relationships list of dicts
        mock_llm.chat_completion.return_value = json.dumps({
            "headline": "Test Headline",
            "summary_sentences": ["Summary 1"],
            "entities": [],
            "relationships": [
                {
                    "source": "Alice", 
                    "target": "Bob", 
                    "relation": "friend", 
                    "description": "Childhood friends"
                },
                {
                    "source": "Bob", 
                    "target": "Charlie", 
                    "relation": "enemy", 
                    "description": "Rivals in business"
                }
            ]
        })
        
        generator = SummaryGenerator(mock_llm)
        chapter = Chapter(id="ch1", title="Test Chapter", content="Alice met Bob...", word_count=100)
        
        summary = generator.generate_summary(chapter)
        
        assert len(summary.relationships) == 2
        
        # Access by index
        rel1 = summary.relationships[0]
        assert rel1.source == "Alice"
        assert rel1.target == "Bob"
        assert rel1.relation == "friend"
        assert rel1.description == "Childhood friends"
        
        rel2 = summary.relationships[1]
        assert rel2.source == "Bob"
        assert rel2.target == "Charlie"
        assert rel2.relation == "enemy"

    def test_parse_malformed_relationships(self):
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = json.dumps({
            "headline": "Test",
            "summary_sentences": [],
            "relationships": [
                {"source": "A", "target": "B"}, # Missing relation/desc
                {"broken": "data"} # Completely wrong
            ]
        })
        
        generator = SummaryGenerator(mock_llm)
        chapter = Chapter(id="ch1", title="Test", content="...", word_count=10)
        summary = generator.generate_summary(chapter)
        
        # Should gracefully handle errors
        # Pydantic validation might fail for missing fields if not optional
        # Let's check our model definition. 
        # In models.py, relation and description are required fields (Field(...)).
        # So the first item should fail validation inside the try-except block in generator.
        
        assert len(summary.relationships) == 0
