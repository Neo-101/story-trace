from typing import List, Tuple
from data_protocol.models import ConceptStage

class ConceptAggregator:
    """
    Aggregator for Concept Evolution (Module 2).
    Tracks how a concept evolves across chapters (Unknown -> Rumor -> Fact -> Truth).
    """
    
    def aggregate_evolution(self, stages: List[Tuple[int, ConceptStage]]) -> List[ConceptStage]:
        """
        Aggregate a list of (chapter_index, ConceptStage) tuples into a sorted list of ConceptStage.
        
        Args:
            stages: List of tuples, each containing a chapter index and a ConceptStage object.
            
        Returns:
            List of ConceptStage objects sorted by chapter index.
        """
        # Sort by chapter index to ensure chronological order
        sorted_stages = sorted(stages, key=lambda x: x[0])
        
        # Return only the ConceptStage objects
        return [stage for _, stage in sorted_stages]
