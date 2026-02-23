from typing import List, Tuple
from data_protocol.models import ClueState

class ClueAggregator:
    """
    负责伏笔（Clue）生命周期的聚合与状态分析。
    """
    def __init__(self):
        pass

    def aggregate_lifecycle(self, events: List[Tuple[int, ClueState]]) -> List[ClueState]:
        """
        将分散的线索事件聚合为按章节排序的生命周期列表。
        
        Args:
            events: (章节索引, 线索状态) 的列表
            
        Returns:
            List[ClueState]: 按章节顺序排列的线索状态列表
        """
        # 按章节索引排序
        # 假设 events 是 [(chapter_index, ClueState), ...]
        sorted_events = sorted(events, key=lambda x: x[0])
        
        # 提取 ClueState 对象
        lifecycle = [event[1] for event in sorted_events]
        
        return lifecycle

    def analyze_status(self, clue_state: ClueState, current_chapter_index: int, threshold: int = 40) -> str:
        """
        分析线索在当前章节的状态。
        如果线索长期处于 'Setup' 状态未被回收，可能被判定为 'Forgotten'。
        
        Args:
            clue_state: 当前线索状态
            current_chapter_index: 当前章节索引
            threshold: 判定为“遗忘”的章节跨度阈值，默认为 40 章
            
        Returns:
            str: 分析后的状态字符串 ("Forgotten" 或 原状态)
        """
        if clue_state.state == "Setup":
            gap = current_chapter_index - clue_state.chapter_index
            if gap > threshold:
                return "Forgotten"
        
        return clue_state.state
