
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_protocol.models import ChapterSummary, AggregatedEntity
from core.world_builder.aggregator import EntityAggregator

def main():
    # Path provided by user: d:\Programming\Tools\split-novel-txt\output\故障烏託邦\8771c958\20260220_001147\summaries.json
    # We'll use a relative path if possible, or just the absolute one for this test
    target_file = r"d:\Programming\Tools\split-novel-txt\output\故障烏託邦\8771c958\20260220_001147\summaries.json"
    
    if not os.path.exists(target_file):
        print(f"Error: File not found: {target_file}")
        return

    print(f"Loading summaries from: {target_file}")
    
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        print(f"Loaded {len(data)} chapters.")
        
        summaries = []
        for item in data:
            # Ensure fields exist
            if "entities" not in item: item["entities"] = []
            if "relationships" not in item: item["relationships"] = []
            summaries.append(ChapterSummary(**item))
            
        aggregator = EntityAggregator()
        entities = aggregator.aggregate_entities(summaries)
        relationships = aggregator.aggregate_relationships(summaries)
        
        print(f"\n--- Graph Statistics ---")
        print(f"Nodes (Aggregated Entities): {len(entities)}")
        print(f"Edges (Aggregated Relationships): {len(relationships)}")
        
        if len(entities) > 0:
            print(f"\n[Sample Node 0]: {entities[0]}")
            
        if len(relationships) > 0:
            print(f"\n[Sample Edge 0]:")
            edge = relationships[0]
            print(f"  Source: {edge.source}")
            print(f"  Target: {edge.target}")
            print(f"  Timeline Events: {len(edge.timeline)}")
            if edge.timeline:
                evt = edge.timeline[0]
                # timeline contains dicts, not objects
                cid = evt.get("chapter_id")
                order = evt.get("order")
                rel = evt.get("relation")
                print(f"    - Event 0: Chapter={cid}, Order={order}, Rel={rel}")
                
        # Check specific chapter 'ch_10' mentioned by user
        ch10 = next((s for s in summaries if s.chapter_id == "ch_10"), None)
        if ch10:
            print(f"\n--- Chapter 10 Analysis ---")
            print(f"Entities: {len(ch10.entities)}")
            print(f"Relationships: {len(ch10.relationships)}")
            if ch10.relationships:
                print(f"Sample Rel: {ch10.relationships[0]}")
        else:
            print("\nChapter 10 not found in summaries.")
            
        # Debug Mismatch Logic
        print("\n--- Mismatch Debug ---")
        summary_ids = set(s.chapter_id for s in summaries)
        print(f"Summary IDs (Total {len(summary_ids)}): {sorted(list(summary_ids))[:5]}...")
        
        timeline_ids = set()
        for edge in relationships:
            for evt in edge.timeline:
                timeline_ids.add(evt.get("chapter_id"))
        
        print(f"Timeline IDs (Total {len(timeline_ids)}): {sorted(list(timeline_ids))[:5]}...")
        
        missing = timeline_ids - summary_ids
        if missing:
            print(f"WARNING: Found {len(missing)} IDs in timeline not present in summaries!")
            print(f"Missing sample: {list(missing)[:5]}")
        else:
            print("SUCCESS: All timeline IDs exist in summary IDs.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
