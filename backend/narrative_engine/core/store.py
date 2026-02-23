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
        # Replace non-alphanumeric chars (except _ and -) with _
        # IMPORTANT: entity_id might contain Chinese characters which are alphanumeric in Unicode.
        # But we want to avoid spaces and slashes.
        # Let's just replace spaces and slashes.
        # Or better: keep Chinese chars.
        
        safe_id = entity_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
        
        path = self.base_path / novel_hash / plugin_type / safe_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_state(self, novel_hash: str, plugin_type: str, entity_id: str, state: BaseNarrativeState):
        """
        Saves a state snapshot to a JSON file.
        Filename: checkpoint_{chapter_index}.json
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, entity_id)
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

    def get_state_at_chapter(
        self,
        novel_hash: str,
        plugin_type: str,
        entity_id: str,
        chapter_index: int,
        model_class: Type[BaseNarrativeState]
    ) -> Optional[BaseNarrativeState]:
        """
        Retrieves the state snapshot EXACTLY AT a given chapter index.
        Used for Cache Hit check.
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, entity_id)
        file_path = entity_dir / f"checkpoint_{chapter_index}.json"
        
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return model_class(**data)
        except Exception as e:
            print(f"[StateStore] Failed to load checkpoint {file_path}: {e}")
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
        # Fix: Ensure glob pattern matches and sorting handles potential non-integer parts gracefully
        files = list(entity_dir.glob("checkpoint_*.json"))
        
        def get_chapter_index(file_path):
            try:
                return int(file_path.stem.split("_")[1])
            except (IndexError, ValueError):
                return -1

        for file in sorted(files, key=get_chapter_index):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Pydantic validation might fail if schema changed
                    states.append(model_class(**data))
            except Exception as e:
                print(f"[StateStore] Warning: Failed to load {file}: {e}")
                continue
        return states

    def delete_history(self, novel_hash: str, plugin_type: str, entity_id: str) -> bool:
        """
        Deletes all history for a specific entity pair.
        Returns True if successful (or directory didn't exist), False on error.
        """
        entity_dir = self._get_entity_dir(novel_hash, plugin_type, entity_id)
        if not entity_dir.exists():
            return True
            
        try:
            # Delete all files in directory
            for file in entity_dir.iterdir():
                if file.is_file():
                    file.unlink()
            
            # Remove directory
            entity_dir.rmdir()
            return True
        except Exception as e:
            print(f"[StateStore] Failed to delete history for {entity_id}: {e}")
            return False
