import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, create_engine
from core.db.engine import engine
from core.db.models import Novel, NovelVersion, AnalysisRun, Chapter, Entity
from core.world_builder.aggregator import EntityAggregator
from backend.routers.analysis import db_chapter_to_summary, get_merged_chapters

def debug_graph_response():
    with Session(engine) as session:
        # 1. Find the target novel version
        # Assuming we are debugging "故障烏託邦"
        novel_name = "故障烏託邦"
        file_hash = "8771c958"
        
        # 2. Get Merged Chapters
        try:
            chapters = get_merged_chapters(session, novel_name, file_hash)
            print(f"Found {len(chapters)} merged chapters.")
        except Exception as e:
            print(f"Error fetching chapters: {e}")
            return

        # 3. Check Entity in DB
        # Find "孙杰克" in Chapter 1
        target_name = "孙杰克"
        
        print("\n--- DB Check ---")
        found_in_db = False
        for ch in chapters:
            for ent in ch.entities:
                if ent.name == target_name:
                    print(f"Found '{target_name}' in Ch {ch.chapter_index}:")
                    print(f"  concept_evolution_json: {ent.concept_evolution_json[:100] if ent.concept_evolution_json else 'None'}")
                    if ent.concept_evolution_json:
                        found_in_db = True
                    break
            if found_in_db:
                break
        
        if not found_in_db:
            print(f"ERROR: '{target_name}' not found or missing concept_evolution_json in DB!")
            return

        # 4. Check Aggregator Logic
        print("\n--- Aggregator Check ---")
        summaries = [db_chapter_to_summary(c) for c in chapters]
        aggregator = EntityAggregator()
        entities = aggregator.aggregate_entities(summaries)
        
        target_entity = next((e for e in entities if e.name == target_name), None)
        
        if not target_entity:
            print(f"ERROR: '{target_name}' not found in aggregated entities!")
            return
            
        print(f"Aggregated Entity '{target_name}':")
        # Check if attribute exists
        if hasattr(target_entity, 'concept_evolution'):
            print(f"  Has 'concept_evolution' attribute: Yes")
            print(f"  Length: {len(target_entity.concept_evolution)}")
            for stage in target_entity.concept_evolution:
                print(f"    - {stage.stage_name}: {stage.description[:50]}...")
        else:
            print(f"  Has 'concept_evolution' attribute: NO")
            print(f"  Attributes: {dir(target_entity)}")

        # 5. Check API Response Simulation
        print("\n--- API Response Simulation ---")
        # Simulate what get_graph_data does
        from backend.schemas import GraphNode
        
        # Attach concept_evolution from ExtendedAggregatedEntity if available
        concept_evolution = getattr(target_entity, 'concept_evolution', None)

        node = GraphNode(
            name=target_entity.name,
            type=target_entity.type,
            description=target_entity.description,
            count=target_entity.count,
            chapter_ids=[], # Dummy
            history=target_entity.history,
            concept_evolution=concept_evolution
        )
        
        json_output = node.model_dump(mode='json')
        print(f"Serialized Node JSON keys: {json_output.keys()}")
        if 'concept_evolution' in json_output:
            print(f"concept_evolution in JSON: {json_output['concept_evolution']}")
        else:
            print("concept_evolution MISSING in JSON output!")

if __name__ == "__main__":
    debug_graph_response()
