import pytest
from core.world_builder.aggregator import EntityAggregator
from data_protocol.models import ChapterSummary, Entity

class TestEntityAggregator:
    
    def test_aggregate_entities(self):
        # 准备测试数据
        summaries = [
            ChapterSummary(
                chapter_id="ch1",
                chapter_title="Chapter 1",
                entities=[
                    Entity(name="孙杰克", type="Person", description="主角", confidence=0.9),
                    Entity(name="塔派", type="Person", description="机器人", confidence=0.8),
                ]
            ),
            ChapterSummary(
                chapter_id="ch2",
                chapter_title="Chapter 2",
                entities=[
                    Entity(name="孙杰克", type="Person", description="主角，非常厉害", confidence=0.9),
                    Entity(name="希尔维亚", type="Person", description="女主角", confidence=0.85),
                ]
            ),
            ChapterSummary(
                chapter_id="ch3",
                chapter_title="Chapter 3",
                entities=[
                    Entity(name="大都会", type="Location", description="赛博朋克城市", confidence=0.9),
                    Entity(name="孙杰克", type="Person", description="主角", confidence=0.9),
                ]
            )
        ]

        aggregator = EntityAggregator()
        result = aggregator.aggregate_entities(summaries)

        # 验证结果
        # 孙杰克(3), 塔派(1), 希尔维亚(1), 大都会(1)
        assert len(result) == 4

        # 验证孙杰克
        sun_jack = next(e for e in result if e.name == "孙杰克")
        assert sun_jack.count == 3
        # chapter_ids is a list of strings
        assert set(sun_jack.chapter_ids) == {"ch1", "ch2", "ch3"}
        assert sun_jack.description == "主角，非常厉害"  # 应该选择了最长的描述

        # 验证塔派
        tapai = next(e for e in result if e.name == "塔派")
        assert tapai.count == 1
        assert tapai.chapter_ids == ["ch1"]

        # 验证排序 (按出现频率)
        assert result[0].name == "孙杰克"  # 出现最多次

    def test_aggregate_empty(self):
        aggregator = EntityAggregator()
        result = aggregator.aggregate_entities([])
        assert result == []

    def test_aggregate_no_entities(self):
        summaries = [
            ChapterSummary(
                chapter_id="ch1",
                chapter_title="Chapter 1",
                entities=[]
            )
        ]
        aggregator = EntityAggregator()
        result = aggregator.aggregate_entities(summaries)
        assert result == []

    def test_aggregate_relationships(self):
        from data_protocol.models import Relationship
        
        summaries = [
            ChapterSummary(
                chapter_id="ch1",
                chapter_title="Chapter 1",
                relationships=[
                    Relationship(source="A", target="B", relation="friend", description="met"),
                    Relationship(source="A", target="B", relation="partner", description="team up")
                ]
            ),
            ChapterSummary(
                chapter_id="ch2",
                chapter_title="Chapter 2",
                relationships=[
                    Relationship(source="B", target="A", relation="enemy", description="betrayal"),
                    Relationship(source="A", target="B", relation="rival", description="fight")
                ]
            )
        ]
        
        aggregator = EntityAggregator()
        result = aggregator.aggregate_relationships(summaries)
        
        # Should have 2 aggregated relationships: (A, B) and (B, A)
        assert len(result) == 2
        
        # Check A->B
        ab = next(r for r in result if r.source == "A" and r.target == "B")
        assert ab.weight == 3
        assert len(ab.timeline) == 3
        assert ab.timeline[0]["chapter_id"] == "ch1"
        assert ab.timeline[0]["relation"] == "friend"
        assert ab.timeline[2]["chapter_id"] == "ch2"
        assert ab.timeline[2]["relation"] == "rival"

        # Check B->A
        ba = next(r for r in result if r.source == "B" and r.target == "A")
        assert ba.weight == 1
        assert ba.timeline[0]["chapter_id"] == "ch2"
        assert ba.timeline[0]["relation"] == "enemy"
