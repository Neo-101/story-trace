from typing import List, Dict, Any
from sqlmodel import Session
from backend.routers.analysis_helper import get_merged_chapters, get_entity_timeline_logic
from backend.schemas import TimelineEvent

class ContextManager:
    """
    Manages context retrieval for LLM analysis, prioritizing cached summaries and timelines
    to minimize input tokens (Strategy: Minimize Input Context).
    """
    
    def __init__(self, session: Session):
        self.session = session
        
    def get_merged_chapters(self, novel_name: str, file_hash: str) -> List[Chapter]:
        """
        Expose merged chapters helper.
        """
        from backend.routers.analysis_helper import get_merged_chapters
        return get_merged_chapters(self.session, novel_name, file_hash)
    
    def get_entity_chronicle(self, novel_name: str, file_hash: str, entity_name: str) -> List[TimelineEvent]:
        """
        Retrieves the Entity Chronicle (Timeline) for a specific entity.
        This serves as the primary input for Concept Evolution analysis.
        """
        chapters = get_merged_chapters(self.session, novel_name, file_hash)
        if not chapters:
            return []
            
        return get_entity_timeline_logic(chapters, entity_name)
    
    def format_chronicle_for_prompt(self, timeline: List[TimelineEvent]) -> str:
        """
        Formats the timeline events into a string suitable for LLM prompt.
        """
        context_str = f"### Entity Chronicle (Time-ordered events)\n"
        
        for event in timeline:
            context_str += f"- Chapter {event.chapter_index} ({event.chapter_title}):\n"
            for content in event.content:
                context_str += f"  * {content}\n"
            context_str += "\n"
            
        return context_str
