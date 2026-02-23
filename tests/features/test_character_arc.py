import pytest
from typing import List, Optional
from backend.narrative_engine.plugins.character_arc import CharacterArcAnalyzer, CharacterArc, CharacterArcPoint

# --- 2. The Test (Behavior Driven) ---

def test_analyze_character_arc_growth():
    """
    Feature: Character Arc Analysis
    Scenario: A character goes from despair to hope (Growth Arc)
    """
    
    # GIVEN: A mock story sequence
    chapters_content = [
        (1, "Alice sat in the dark room, feeling completely hopeless. 'I can't go on,' she whispered."),
        (2, "Alice found a small key. It didn't fit, but it gave her a glimmer of an idea."),
        (3, "Alice unlocked the door and stepped into the sunlight. She knew she could face whatever came next.")
    ]
    
    character_name = "Alice"
    
    # WHEN: We analyze the arc (This function doesn't exist yet!)
    # We are mocking the LLM/Analysis engine here to define the contract.
    # In a real integration test, we might use a mock LLM that returns pre-defined JSON.
    
    from backend.narrative_engine.plugins.character_arc import CharacterArcAnalyzer
    analyzer = CharacterArcAnalyzer()
    
    # We expect the analyzer to take a list of (index, text) and a character name
    arc = analyzer.analyze_arc(character_name, chapters_content)
    
    # THEN: The result should reflect a Growth arc
    assert isinstance(arc, CharacterArc)
    assert arc.character_name == "Alice"
    assert len(arc.points) == 3
    
    # Check emotional progression
    assert arc.points[0].emotion_score < 0  # Starts negative (despair)
    assert arc.points[2].emotion_score > 0  # Ends positive (hope)
    assert arc.points[2].emotion_score > arc.points[0].emotion_score # Upward trend
    
    # Check Arc Type
    assert arc.arc_type == "Growth"
    
    # Check motivations
    assert "hopeless" in arc.points[0].state_description.lower() or "despair" in arc.points[0].state_description.lower()
    assert "face" in arc.points[2].state_description.lower() or "confident" in arc.points[2].state_description.lower()
