import json
import os
from typing import Optional, List, Type
from pathlib import Path
from backend.narrative_engine.core.models import BaseNarrativeState, RelationshipState

class StateStore:
    """
    Persistence layer for Narrative States.
    Uses a file-based JSON storage for now (simplest for incremental updates).
    """
    def __init__(self, base_path: str = "cache/narrative"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_entity_dir(self, novel_hash: str, plugin_type: str, entity_id: str) -> Path:
        """
        Constructs the storage path: cache/narrative/{hash}/{plugin}/{entity_id}/
        """
        # Sanitize entity_id for filesystem
        safe_id = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in entity_id])
        path = self.base_path / novel_hash / plugin_type / safe_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_state(self, novel_hash: str, plugin_type: str, state: BaseNarrativeState):
        """
        Saves a state snapshot to a JSON file.
        Filename: checkpoint_{chapter_index}.json
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, state.entity_id)
        file_path = entity_dir / f"checkpoint_{state.chapter_index}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            # Pydantic v2 compatible dump
            f.write(state.model_dump_json(indent=2))
            
    def get_latest_state(
        self, 
        novel_hash: str, 
        plugin_type: str, 
        entity_id: str, 
        before_chapter: int,
        model_class: Type[BaseNarrativeState]
    ) -> Optional[BaseNarrativeState]:
        """
        Retrieves the latest state snapshot BEFORE a given chapter index.
        Used to provide context for analyzing chapter N.
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, entity_id)
        if not entity_dir.exists():
            return None
            
        # Find all checkpoints
        checkpoints = []
        for file in entity_dir.glob("checkpoint_*.json"):
            try:
                # Parse index from filename "checkpoint_123.json"
                idx = int(file.stem.split("_")[1])
                if idx < before_chapter:
                    checkpoints.append((idx, file))
            except (ValueError, IndexError):
                continue
                
        if not checkpoints:
            return None
            
        # Sort by index descending (get the latest one)
        checkpoints.sort(key=lambda x: x[0], reverse=True)
        latest_file = checkpoints[0][1]
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return model_class(**data)
        except Exception as e:
            print(f"[StateStore] Failed to load checkpoint {latest_file}: {e}")
            return None

    def list_history(
        self, 
        novel_hash: str, 
        plugin_type: str, 
        entity_id: str,
        model_class: Type[BaseNarrativeState]
    ) -> List[BaseNarrativeState]:
        """
        Returns the full history of states for an entity, sorted by chapter.
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, entity_id)
        if not entity_dir.exists():
            return []
            
        states = []
        for file in sorted(entity_dir.glob("checkpoint_*.json"), key=lambda f: int(f.stem.split("_")[1])):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    states.append(model_class(**data))
            except Exception:
                continue
        return states
