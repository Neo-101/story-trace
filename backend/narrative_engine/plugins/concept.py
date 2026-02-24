from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from core.db.models import Chapter, Novel, NovelVersion, AnalysisRun
from data_protocol.models import ConceptStage
from backend.narrative_engine.core.context_manager import ContextManager
from backend.narrative_engine.prompts import CONCEPT_EVOLUTION_TEMPLATE
import json

class ConceptAnalyzer:
    """
    Analyzes the evolution of a concept (entity) across the entire narrative timeline.
    Uses 'Entity Chronicle' as context to minimize input tokens.
    Detects stages: Unknown -> Rumor -> Fact -> Truth.
    """
    
    def __init__(self, session: Session, llm_client: Any):
        self.session = session
        self.llm_client = llm_client
        self.context_manager = ContextManager(session)

    def analyze_entity(self, novel_name: str, file_hash: str, entity_name: str, force: bool = False) -> List[ConceptStage]:
        """
        Main entry point for Concept Evolution Analysis.
        1. Fetches entity timeline (chronicle).
        2. Generates prompt with chronicle as context.
        3. Calls LLM to identify stages.
        4. Updates relevant chapters in DB with new ConceptStage info.
        
        Args:
            force: If True, ignores existing data and re-analyzes.
        """
        # 0. Check Idempotency (Skip if data exists and not forced)
        if not force:
            has_data = self._check_entity_has_concept_data(novel_name, file_hash, entity_name)
            if has_data:
                return self._fetch_existing_concept_data(novel_name, file_hash, entity_name)

        # 1. Get Context (Minimize Input)
        timeline = self.context_manager.get_entity_chronicle(novel_name, file_hash, entity_name)
        if not timeline:
            print(f"No timeline found for entity: {entity_name}")
            return []

        chronicle_text = self.context_manager.format_chronicle_for_prompt(timeline)

        # 2. Generate Prompt
        prompt = CONCEPT_EVOLUTION_TEMPLATE.format(
            entity_name=entity_name,
            chronicle_text=chronicle_text
        )

        # 3. Call LLM
        try:
            # Assumes llm_client has a .generate(prompt) method
            response = self.llm_client.generate(prompt)
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return []
        
        # 4. Parse Response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            stages_data = json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse LLM response: {e}\nResponse was: {response}")
            return []

        # 4.5 Clear existing concept data for this entity across ALL chapters (Full Replacement)
        self._clear_entity_concept_data(novel_name, file_hash, entity_name)

        # 5. Save to DB
        updated_stages = []

        for stage_data in stages_data:
            chapter_index = stage_data.get("chapter_index")
            if chapter_index is None:
                continue
                
            # Construct ConceptStage object
            stage = ConceptStage(
                stage_name=stage_data.get("stage_name", "Unknown"),
                description=stage_data.get("description", ""),
                revealed_by=stage_data.get("revealed_by", [])
            )
            
            self._save_stage_to_chapter(novel_name, file_hash, chapter_index, entity_name, stage)
            updated_stages.append(stage)
            
        return updated_stages

    def _check_entity_has_concept_data(self, novel_name: str, file_hash: str, entity_name: str) -> bool:
        """
        Checks if the entity already has concept evolution data.
        """
        from core.db.models import Entity
        chapters = self.context_manager.get_merged_chapters(novel_name, file_hash)
        if not chapters:
            return False
            
        chapter_ids = [c.id for c in chapters]
        
        # Check if concept_evolution_json contains valid data (not just empty list)
        statement = select(Entity).where(
            Entity.chapter_id.in_(chapter_ids),
            Entity.name == entity_name,
            Entity.concept_evolution_json.is_not(None),
            Entity.concept_evolution_json != "[]" 
        ).limit(1)
        
        result = self.session.exec(statement).first()
        return result is not None

    def _fetch_existing_concept_data(self, novel_name: str, file_hash: str, entity_name: str) -> List[ConceptStage]:
        """
        Fetches and aggregates existing concept data for an entity.
        Essentially re-does the aggregation logic but for a single entity.
        """
        # Note: We can reuse the Aggregator logic!
        # But Aggregator processes ALL entities.
        # Let's just do a mini-aggregation here.
        
        chapters = self.context_manager.get_merged_chapters(novel_name, file_hash)
        raw_stages = []
        
        for chapter in chapters:
            for e in chapter.entities:
                if e.name == entity_name and e.concept_evolution_json:
                    try:
                        stages = json.loads(e.concept_evolution_json)
                        for stage_dict in stages:
                            # Handle both dict and object
                            if isinstance(stage_dict, dict):
                                stage = ConceptStage(**stage_dict)
                            else:
                                stage = stage_dict
                            raw_stages.append((chapter.chapter_index, stage))
                    except:
                        pass
                        
        # Use Aggregator's logic to sort
        from core.world_builder.concept_aggregator import ConceptAggregator
        aggregator = ConceptAggregator()
        return aggregator.aggregate_evolution(raw_stages)

    def _clear_entity_concept_data(self, novel_name: str, file_hash: str, entity_name: str):
        """
        Clears concept_evolution_json for the specified entity across all chapters in the latest run.
        This ensures we don't accumulate duplicate or stale data.
        """
        from core.db.models import Entity
        
        # We need to find all entities with this name in the latest run chapters
        # Since we can't easily join everything in one update statement in SQLModel/SQLAlchemy core without complex logic,
        # we will iterate. For performance, we could do a bulk update if we had the IDs.
        
        # 1. Get merged chapters first to know which chapters are active
        chapters = self.context_manager.get_merged_chapters(novel_name, file_hash)
        if not chapters:
            return

        chapter_ids = [c.id for c in chapters]
        
        # 2. Find entities in these chapters matching the name
        # Use simpler normalization check if possible, or just strict name match for now as per logic
        # Ideally we should use the same normalization logic as aggregator
        
        # Let's fetch all entities with this name in these chapters
        statement = select(Entity).where(
            Entity.chapter_id.in_(chapter_ids),
            Entity.name == entity_name
        )
        entities = self.session.exec(statement).all()
        
        for e in entities:
            e.concept_evolution_json = None # Clear it
            self.session.add(e)
            
        self.session.commit()
        # print(f"Cleared concept data for {entity_name} in {len(entities)} chapters")

    def _save_stage_to_chapter(self, novel_name: str, file_hash: str, chapter_index: int, entity_name: str, stage: ConceptStage):
        """
        Updates the entity record in the specified chapter with the new concept stage.
        """
        # Find the latest run's chapter for this index
        statement = select(Chapter).join(AnalysisRun).join(NovelVersion).join(Novel).where(
            Novel.name == novel_name,
            NovelVersion.hash == file_hash,
            Chapter.chapter_index == chapter_index
        ).order_by(AnalysisRun.timestamp.desc())
        
        chapter = self.session.exec(statement).first()
        
        if not chapter:
            print(f"Chapter {chapter_index} not found for {novel_name}")
            return

        # Find target entity in this chapter
        target_entity = None
        
        # Try exact match first
        for e in chapter.entities:
            if e.name == entity_name: 
                target_entity = e
                break
        
        # If not found, try simpler normalization (strip whitespace)
        if not target_entity:
            for e in chapter.entities:
                if e.name.strip() == entity_name.strip():
                    target_entity = e
                    break
        
        if target_entity:
            # Update concept_evolution_json
            current_evolution = []
            if target_entity.concept_evolution_json:
                try:
                    current_evolution = json.loads(target_entity.concept_evolution_json)
                except:
                    pass
            
            # Check for duplicates to avoid bloating
            is_duplicate = False
            stage_dict = stage.model_dump()
            
            for s in current_evolution:
                # Basic duplicate check: same stage name and description
                if s.get("stage_name") == stage.stage_name and s.get("description") == stage.description:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                current_evolution.append(stage_dict)
                target_entity.concept_evolution_json = json.dumps(current_evolution, ensure_ascii=False)
                self.session.add(target_entity)
                self.session.commit()
                self.session.refresh(target_entity)
                # print(f"Updated entity {entity_name} in Ch{chapter_index} with stage {stage.stage_name}")
