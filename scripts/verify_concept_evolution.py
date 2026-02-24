import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_protocol.models import ConceptStage, Entity
from core.world_builder.concept_aggregator import ConceptAggregator

# --- Mock Data Definition ---
STAGES_INPUT = [
    (1, ConceptStage(
        stage_name="Unknown",
        description="系统似乎是一个无处不在的控制网络，但具体运作方式不明。",
        revealed_by=["第1章: 孙杰克初次醒来时的电子提示音"]
    )),
    (5, ConceptStage(
        stage_name="Rumor",
        description="传闻系统会根据每个人的贡献度分配资源，底层人几乎无法翻身。",
        revealed_by=["第5章: 疯子的胡言乱语", "第6章: 街头广告"]
    )),
    (10, ConceptStage(
        stage_name="Fact",
        description="系统通过神经接口直接干预市民行为，任何违规都会被实时记录。",
        revealed_by=["第10章: 执法机器人的行动逻辑"]
    )),
    (15, ConceptStage(
        stage_name="Truth",
        description="系统的本质是一个巨大的生物计算机，利用人类大脑作为算力节点。",
        revealed_by=["第15章: 发现废弃服务器室的秘密文件"]
    ))
]

DATA_PATH = Path("output/故障烏託邦/8771c958/20260222_111350/summaries.json")

def main():
    print(f"Loading data from {DATA_PATH}...")
    if not DATA_PATH.exists():
        print("Error: Data file not found.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Aggregate Concepts
    aggregator = ConceptAggregator()
    evolution = aggregator.aggregate_evolution(STAGES_INPUT)
    
    print(f"Aggregated {len(evolution)} stages.")

    # 2. Inject into EXISTING Entity
    # We choose "孙杰克" (Sun Jieke) because he is the protagonist and guaranteed to exist in Chapter 1.
    target_entity_name = "孙杰克"
    found_count = 0
    
    for chapter in data:
        if "entities" in chapter:
            for entity in chapter["entities"]:
                if entity["name"] == target_entity_name:
                    print(f"Injecting concept evolution into '{target_entity_name}' in Chapter {chapter.get('chapter_id')}...")
                    entity["concept_evolution"] = [stage.model_dump() for stage in evolution]
                    found_count += 1
    
    if found_count == 0:
        print(f"Warning: Target entity '{target_entity_name}' not found. Creating a dummy one.")
        if data:
             data[0]["entities"].append({
                "name": target_entity_name,
                "type": "Person",
                "description": "The Protagonist",
                "concept_evolution": [stage.model_dump() for stage in evolution]
             })
             found_count += 1
                        
    print(f"Injected into {found_count} occurrences of '{target_entity_name}'.")

    # 3. Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Success! Data injected.")
    print(f"Please check the '{target_entity_name}' node in the graph.")

if __name__ == "__main__":
    main()
