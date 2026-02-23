from typing import List, Tuple
from data_protocol.models import FactionInfo

class FactionAggregator:
    """
    Aggregator for Faction Dynamics (Module 4).
    Tracks faction territories, enemies, and allies across chapters.
    """
    
    def aggregate_history(self, updates: List[Tuple[int, FactionInfo]]) -> List[FactionInfo]:
        """
        Aggregate a list of (chapter_index, FactionInfo) tuples into a sorted history list.
        
        Args:
            updates: List of tuples, each containing a chapter index and a FactionInfo object.
            
        Returns:
            List of FactionInfo objects sorted by chapter index.
        """
        # Sort by chapter index to ensure chronological order
        sorted_updates = sorted(updates, key=lambda x: x[0])
        
        # Return only the FactionInfo objects
        return [info for _, info in sorted_updates]
