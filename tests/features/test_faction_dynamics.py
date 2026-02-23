import pytest
from typing import List
from pydantic import BaseModel, Field
from data_protocol.models import FactionInfo, ExtendedAggregatedEntity

# --- Spec: Module 4 - Faction Dynamics ---
# Goal: Track territories, enemies, and allies of factions.

def test_faction_territory_expansion():
    """
    Feature: Faction Territory Tracking
    Scenario: A faction expands its control over time.
    """
    
    # GIVEN: LLM extraction results for different chapters
    
    # Chapter 1: Initial state
    ch1_faction = FactionInfo(
        faction_name="The Resistance",
        territory=["Slums", "Underground Sewers"],
        enemies=["The Empire"],
        allies=["Smugglers"]
    )
    
    # Chapter 5: Conquest
    ch5_faction = FactionInfo(
        faction_name="The Resistance",
        territory=["Slums", "Underground Sewers", "Central Plaza"], # Added Plaza
        enemies=["The Empire", "City Guard"], # Added Guard
        allies=["Smugglers"]
    )
    
    # WHEN: We aggregate the faction history
    from core.world_builder.faction_aggregator import FactionAggregator # To be implemented
    aggregator = FactionAggregator()
    
    history = aggregator.aggregate_history([
        (1, ch1_faction),
        (5, ch5_faction)
    ])
    
    # THEN: The history should show expansion
    assert len(history) == 2
    
    # AND: The final entity should reflect the current territory (latest snapshot)
    final_entity = ExtendedAggregatedEntity(
        name="The Resistance",
        type="Organization",
        description="...",
        faction="The Resistance", # Self-reference
        # territory=... (Need to decide if ExtendedAggregatedEntity has a dedicated territory field or if FactionInfo is embedded)
        # Assuming FactionInfo is embedded or linked
    )
    
    # Wait, ExtendedAggregatedEntity only has 'faction' string field currently.
    # We might need to extend ExtendedAggregatedEntity to hold FactionInfo details if it IS a faction itself.
    # Or store FactionInfo separately.
    # For now, let's assume the aggregator returns a list of FactionInfo snapshots.
    
    latest_state = history[-1]
    assert "Central Plaza" in latest_state.territory
    assert "City Guard" in latest_state.enemies

def test_faction_alliance_shift():
    """
    Scenario: An ally becomes an enemy.
    """
    ch1 = FactionInfo(
        faction_name="Kingdom A",
        allies=["Kingdom B"],
        enemies=[]
    )
    
    ch10 = FactionInfo(
        faction_name="Kingdom A",
        allies=[],
        enemies=["Kingdom B"] # Betrayal!
    )
    
    from core.world_builder.faction_aggregator import FactionAggregator
    aggregator = FactionAggregator()
    
    history = aggregator.aggregate_history([(1, ch1), (10, ch10)])
    
    latest = history[-1]
    assert "Kingdom B" in latest.enemies
    assert "Kingdom B" not in latest.allies
