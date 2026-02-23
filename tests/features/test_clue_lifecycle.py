import pytest
from typing import List
from pydantic import BaseModel, Field
from data_protocol.models import ClueState, ExtendedAggregatedEntity

# --- Spec: Module 3 - Clue Lifecycle (Chekhov's Gun) ---
# Goal: Track an item from Setup -> Reminder -> Payoff -> Forgotten

def test_clue_lifecycle_full_cycle():
    """
    Feature: Clue Lifecycle Tracking
    Scenario: A gun is hung on the wall (Setup) and later fired (Payoff).
    """
    
    # GIVEN: LLM extraction results for different chapters
    
    # Chapter 1: Setup
    setup = ClueState(
        state="Setup",
        chapter_index=1,
        context="A rusty shotgun hangs above the fireplace, seemingly decorative."
    )
    
    # Chapter 10: Reminder
    reminder = ClueState(
        state="Reminder",
        chapter_index=10,
        context="The protagonist glances at the shotgun while pacing nervously."
    )
    
    # Chapter 25: Payoff
    payoff = ClueState(
        state="Payoff",
        chapter_index=25,
        context="She grabs the shotgun and fires at the intruder. It works!"
    )
    
    # WHEN: We aggregate the lifecycle
    from core.world_builder.clue_aggregator import ClueAggregator # To be implemented
    aggregator = ClueAggregator()
    
    lifecycle = aggregator.aggregate_lifecycle([
        (1, setup),
        (10, reminder),
        (25, payoff)
    ])
    
    # THEN: The lifecycle should be complete and ordered
    assert len(lifecycle) == 3
    assert lifecycle[0].state == "Setup"
    assert lifecycle[1].state == "Reminder"
    assert lifecycle[2].state == "Payoff"
    
    # AND: The final entity should be marked as "Resolved" or similar logic
    entity = ExtendedAggregatedEntity(
        name="Rusty Shotgun",
        type="Item",
        description="...",
        clue_lifecycle=lifecycle
    )
    # assert entity.is_resolved == True

def test_clue_forgotten_detection():
    """
    Scenario: A clue is setup but never used.
    If Chapter 50 passes without a Payoff for a Setup in Chapter 1, it might be forgotten.
    This requires a more complex check (maybe based on chapter gap).
    """
    setup = ClueState(
        state="Setup",
        chapter_index=1,
        context="A mysterious key found in the drawer."
    )
    
    from core.world_builder.clue_aggregator import ClueAggregator
    aggregator = ClueAggregator()
    
    # Analyze against a current chapter of 50
    status = aggregator.analyze_status(setup, current_chapter_index=50)
    
    assert status == "Forgotten" or status == "Pending Long-term Payoff"
