
import sys
import os
from typing import List, Dict
from sqlmodel import Session, select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.engine import engine
from core.db.models import Chapter, Novel, NovelVersion
from backend.routers.analysis import db_chapter_to_summary
from core.world_builder.aggregator import EntityAggregator

def debug_logic():
    with Session(engine) as session:
        # 1. Simulate list_chapters
        # Find ANY run
        from core.db.models import AnalysisRun
        run = session.exec(select(AnalysisRun)).first()
        if not run:
            print("No run found! But diagnose_db showed chapters?")
            # Maybe chapters are orphaned?
            chapters = session.exec(select(Chapter)).all()
            print(f"Found {len(chapters)} orphaned chapters?")
            return

        print(f"Found Run ID: {run.id}")
        
        # Get chapters for this run
        chapters = run.chapters
        # Sort by index
        chapters.sort(key=lambda c: c.chapter_index)
        
        print(f"Loaded {len(chapters)} chapters from Run {run.id}.")
        
        # 2. Build chapterIdToIndex (Frontend logic simulation)
        # Map<string, number>
        chapter_id_to_index = {}
        for i, c in enumerate(chapters):
            # Frontend uses String(c.id)
            c_id_str = str(c.id)
            chapter_id_to_index[c_id_str] = i
            print(f"Index {i}: Ch {c.chapter_index} (ID: {c_id_str})")

        # 3. Get Graph Data
        summaries = [db_chapter_to_summary(c) for c in chapters]
        aggregator = EntityAggregator()
        # entities = aggregator.aggregate_entities(summaries) 
        relationships = aggregator.aggregate_relationships(summaries)
        
        print(f"\nAggregated {len(relationships)} relationships.")
        
        # 4. Simulate Filtering for Ch 13 (Index 12)
        timeline_index = 12
        print(f"\n--- Simulating Timeline Index {timeline_index} (Ch 13) ---")
        
        active_edges_count = 0
        total_weight = 0
        
        for edge in relationships: # AggregatedRelationship
            weight = 0
            # edge.timeline is a list of dicts
            for event in edge.timeline:
                # event['chapter_id'] is the DB ID (str)
                evt_chap_id = str(event['chapter_id'])
                
                evt_idx = chapter_id_to_index.get(evt_chap_id)
                
                if evt_idx is not None and evt_idx <= timeline_index:
                    weight += 1 # Simplified weight logic
                    
            if weight > 0:
                active_edges_count += 1
                total_weight += weight
                
        print(f"Active Edges: {active_edges_count}")
        print(f"Total Weight: {total_weight}")
        
        if active_edges_count == 0:
            print("!!! PROBLEM REPRODUCED: No active edges found for Ch 13 !!!")
            # Debug why
            print("\nDebugging first 5 edges:")
            for i, edge in enumerate(relationships[:5]):
                print(f"Edge {i}: {edge.source} -> {edge.target}")
                for event in edge.timeline:
                    eid = str(event['chapter_id'])
                    idx = chapter_id_to_index.get(eid)
                    print(f"  Event Ch ID: {eid} -> Index: {idx}")
        else:
            print("Logic seems correct in Python. Issue might be JS specific.")

if __name__ == "__main__":
    debug_logic()
