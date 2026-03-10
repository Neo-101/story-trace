from typing import List, Dict

import hashlib

class Prompts:
    """Prompt 模板管理"""
    
    SYSTEM_PROMPT = """你是一个专业的文学分析师。你的任务是对给定的小说章节进行总结，并提取其中的关键实体。
请遵循以下规则，涵盖小说的三要素（人物、情节、环境）：

### 1. 情节 (Story/Plot)
*   总结应概括本章的核心事件、人物互动和重要情节转折。
*   总结应该分为若干个独立的句子，每个句子描述一个具体的事件点。
*   **严禁在总结中重复章节标题**（如“本章标题是xxx”），直接开始总结情节。

### 2. 人物 (Characters)
*   提取本章出现的关键人物，标记为 'Person' 类型。
*   描述中应包含人物的身份、性格特征或本章中的重要行为。

### 3. 环境 (Environment/Setting)
*   提取本章出现的关键地点或环境描写，标记为 'Location' 类型。
*   提取社会环境（如组织、门派、国家），标记为 'Organization' 类型。
*   提取关键物品（道具、武器），标记为 'Item' 类型。
*   提取特殊概念（功法、境界、设定），标记为 'Concept' 类型。

### 4. 关系 (Relationships)
*   提取本章内发生的显式人物互动或实体关系。
*   关系三元组格式: (Source, Relation, Target)。
*   例如: ("张三", "攻击", "李四"), ("王五", "加入", "青云门")。
*   仅提取本章明确提及的重要关系。

### 通用规则
*   保持客观、准确，不要添加个人的主观评价。
*   输出格式必须是 JSON 对象，包含 'headline', 'summary_sentences', 'entities' 和 'relationships'。
*   如果章节内容为空或无实质情节，请返回空 JSON。
*   IMPORTANT: Output ONLY the JSON object. Do not include any explanations, thinking process (<think>...</think>), or markdown formatting outside the JSON.
"""

    USER_PROMPT_TEMPLATE = """请总结以下小说章节的内容，并基于“小说三要素”提取实体：

标题：{title}
内容：
{content}

请输出 JSON 格式，例如：
{{
    "headline": "张三离家出走并结识了李四。",
    "summary_sentences": ["张三离开了家乡。", "他在路上遇到了李四。", "两人决定结伴同行。"],
    "entities": [
        {{"name": "张三", "type": "Person", "description": "主角，性格坚毅，决定离开家乡闯荡"}},
        {{"name": "李四", "type": "Person", "description": "路遇的神秘剑客，外表冷漠"}},
        {{"name": "青云山", "type": "Location", "description": "故事开始的地方，终年云雾缭绕"}},
        {{"name": "青云门", "type": "Organization", "description": "当地的第一大修仙门派"}},
        {{"name": "青云剑", "type": "Item", "description": "李四随身携带的武器"}}
    ],
    "relationships": [
        {{"source": "张三", "relation": "遇见", "target": "李四", "description": "在山脚下偶遇"}},
        {{"source": "张三", "relation": "前往", "target": "青云山", "description": "为了拜师学艺"}},
        {{"source": "李四", "relation": "持有", "target": "青云剑", "description": "随身佩戴"}}
    ]
}}
"""

    @classmethod
    def get_prompt_hash(cls) -> str:
        """计算 Prompt 模板的哈希值，用于缓存校验"""
        content = cls.SYSTEM_PROMPT + cls.USER_PROMPT_TEMPLATE
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def get_summary_prompt(title: str, content: str) -> List[Dict[str, str]]:

        """生成用于总结的 Prompt"""
        return [
            {"role": "system", "content": Prompts.SYSTEM_PROMPT},
            {"role": "user", "content": Prompts.USER_PROMPT_TEMPLATE.format(title=title, content=content)}
        ]

    SEGMENT_SYSTEM_PROMPT = """你是一个专业的小说编辑。你的任务是将一系列连续章节的摘要合并为一个连贯的“剧情段落梗概”。
请遵循以下规则：
1. **高度概括**: 不要流水账式地罗列每章内容，而是提炼出这一段剧情的核心冲突、转折和结果。
2. **字数限制**: 梗概控制在 100-150 字以内。
3. **小标题**: 为这一段剧情起一个简短有力的小标题（4-8字），例如“营救行动”、“黑客入侵”、“初入江湖”。
4. **输出格式**: 必须是 JSON 对象，包含 'title' 和 'synopsis'。
"""

    SEGMENT_USER_TEMPLATE = """以下是小说中一段连续章节的摘要，请为其生成段落小标题和核心梗概：

{summaries}

请输出 JSON 格式：
{{
    "title": "...",
    "synopsis": "..."
}}
"""

    ARC_SYSTEM_PROMPT = """你是一个专业的小说架构师。你的任务是将一系列“剧情段落”的梗概合并为一个宏大的“剧情弧 (Story Arc)”总结。
请遵循以下规则：
1. **宏观视角**: 你不再关注具体的打斗或对话，而是关注人物命运的转折、势力的消长、谜题的揭晓。
2. **字数限制**: 梗概控制在 150-200 字以内。
3. **大标题**: 为这一大段剧情起一个富有史诗感的大标题（2-6字），例如“逃离地球”、“第一滴血”、“觉醒时刻”。
4. **输出格式**: 必须是 JSON 对象，包含 'title' 和 'synopsis'。
"""

    ARC_USER_TEMPLATE = """以下是小说中一段连续剧情段落的梗概，请为其生成剧情弧标题和核心总结：

{summaries}

请输出 JSON 格式：
{{
    "title": "...",
    "synopsis": "..."
}}
"""

    @staticmethod
    def get_segment_summary_prompt(summaries: List[str]) -> List[Dict[str, str]]:
        """生成段落总结 Prompt"""
        content = "\n\n".join(summaries)
        return [
            {"role": "system", "content": Prompts.SEGMENT_SYSTEM_PROMPT},
            {"role": "user", "content": Prompts.SEGMENT_USER_TEMPLATE.format(summaries=content)}
        ]

    @staticmethod
    def get_arc_summary_prompt(segment_summaries: List[str]) -> List[Dict[str, str]]:
        """生成 Arc 总结 Prompt"""
        content = "\n\n".join(segment_summaries)
        return [
            {"role": "system", "content": Prompts.ARC_SYSTEM_PROMPT},
            {"role": "user", "content": Prompts.ARC_USER_TEMPLATE.format(summaries=content)}
        ]
