from abc import ABC, abstractmethod
from typing import Type, List, Optional
from backend.narrative_engine.core.models import BaseNarrativeState

class NarrativePlugin(ABC):
    """
    Abstract interface for all narrative plugins (Relationship, World, Item, Faction).
    Each plugin defines how to analyze its specific type of entity.
    """
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """e.g. 'relationship', 'world', 'item'"""
        pass
        
    @property
    @abstractmethod
    def state_model(self) -> Type[BaseNarrativeState]:
        """Pydantic model class for the state"""
        pass
        
    @abstractmethod
    def get_initial_state(self, entity_id: str, **kwargs) -> BaseNarrativeState:
        """Returns a blank/initial state for a new entity"""
        pass
        
    @abstractmethod
    def check_trigger(self, prev_state: BaseNarrativeState, new_events: List[dict]) -> bool:
        """
        Adaptive Triggering Logic.
        Returns True if LLM analysis is needed.
        Returns False if we can skip/clone the previous state.
        """
        pass
        
    @abstractmethod
    def generate_prompt(self, prev_state: BaseNarrativeState, new_events: List[dict]) -> str:
        """Constructs the prompt for the LLM"""
        pass
        
    @abstractmethod
    def parse_response(self, llm_response: str, base_state: BaseNarrativeState) -> BaseNarrativeState:
        """Parses LLM JSON response into a State object"""
        pass
