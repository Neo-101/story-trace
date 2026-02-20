import json
import jieba
from collections import defaultdict
from typing import List, Tuple, Set
from core.summarizer.llm_client import LLMClient
from core.summarizer.prompts import Prompts
from data_protocol.models import Chapter, ChapterSummary, SummarySentence, TextSpan, Entity, Relationship

STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就",
    "不", "人", "都", "一", "一个", "上", "也", "很",
    "到", "说", "要", "去", "你", "会", "着", "没有",
    "看", "好", "自己", "这", "那", "之", "与", "及"
}

class SummaryGenerator:
    """总结生成器，负责调用 LLM 并提取原文溯源"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate_summary_async(self, chapter: Chapter) -> ChapterSummary:
        """异步为单个章节生成总结"""
        print(f"正在总结章节: {chapter.title} (字数: {chapter.word_count})")
        
        # 1. 调用 LLM 生成总结文本 (异步)
        prompt_messages = Prompts.get_summary_prompt(chapter.title, chapter.content[:4000])
        headline = None
        summary_texts = []
        entities_data = []
        relationships_data = [] # Add initialization
        
        try:
            # Check if client supports async
            if hasattr(self.llm, 'chat_completion_async'):
                raw_response = await self.llm.chat_completion_async(prompt_messages)
            else:
                # Fallback to sync if async not implemented (though it should be)
                import asyncio
                loop = asyncio.get_event_loop()
                raw_response = await loop.run_in_executor(None, self.llm.chat_completion, prompt_messages)

            parsed_data = self._parse_json_response(raw_response)
            
            if isinstance(parsed_data, dict):
                headline = parsed_data.get("headline")
                summary_texts = parsed_data.get("summary_sentences", [])
                entities_data = parsed_data.get("entities", [])
                relationships_data = parsed_data.get("relationships", [])
            elif isinstance(parsed_data, list):
                summary_texts = parsed_data
                if summary_texts:
                    headline = summary_texts[0]
            else:
                summary_texts = [str(parsed_data)]
                
        except Exception as e:
            print(f"LLM 响应解析失败: {e}")
            summary_texts = ["(总结生成失败)"]

        # 2. 溯源匹配 (CPU-bound, can keep sync or run in executor if slow)
        # For simplicity, we keep it sync as it's usually fast enough for now
        summary_objects = []
        if not isinstance(summary_texts, list):
            summary_texts = [str(summary_texts)]

        for text in summary_texts:
            spans = self._find_source_spans(text, chapter.content)
            summary_objects.append(SummarySentence(
                summary_text=text,
                source_spans=spans,
                confidence=1.0 if spans else 0.5
            ))

        # 3. 构建实体对象
        entity_objects = []
        for ent in entities_data:
            try:
                entity_objects.append(Entity(
                    name=ent.get("name", "Unknown"),
                    type=ent.get("type", "Other"),
                    description=ent.get("description", ""),
                    confidence=0.9
                ))
            except Exception as e:
                print(f"实体解析失败: {ent}, error: {e}")

        # 4. 构建关系对象
        relationship_objects = []
        for rel in relationships_data:
            try:
                source = rel.get("source", "").strip()
                target = rel.get("target", "").strip()
                relation = rel.get("relation", "").strip()
                description = rel.get("description", "").strip()
                
                if not source or not target or not relation:
                    continue
                    
                relationship_objects.append(Relationship(
                    source=source,
                    target=target,
                    relation=relation,
                    description=description,
                    confidence=0.9
                ))
            except Exception as e:
                print(f"关系解析失败: {rel}, error: {e}")

        return ChapterSummary(
            chapter_id=chapter.id,
            chapter_title=chapter.title,
            headline=headline,
            summary_sentences=summary_objects,
            entities=entity_objects,
            relationships=relationship_objects
        )

    def generate_summary(self, chapter: Chapter) -> ChapterSummary:
        """为单个章节生成总结"""
        print(f"正在总结章节: {chapter.title} (字数: {chapter.word_count})")
        
        # 1. 调用 LLM 生成总结文本
        prompt_messages = Prompts.get_summary_prompt(chapter.title, chapter.content[:4000]) # 限制长度以避免超 token
        headline = None
        summary_texts = []
        entities_data = []
        
        try:
            raw_response = self.llm.chat_completion(prompt_messages)
            parsed_data = self._parse_json_response(raw_response)
            
            if isinstance(parsed_data, dict):
                headline = parsed_data.get("headline")
                summary_texts = parsed_data.get("summary_sentences", [])
                entities_data = parsed_data.get("entities", [])
                relationships_data = parsed_data.get("relationships", [])
            elif isinstance(parsed_data, list):
                # 兼容旧格式（如果是 list，则视为 detailed summaries）
                summary_texts = parsed_data
                # 尝试用第一句作为 headline 的 fallback
                if summary_texts:
                    headline = summary_texts[0]
            else:
                summary_texts = [str(parsed_data)]
                
        except Exception as e:
            print(f"LLM 响应解析失败: {e}")
            summary_texts = ["(总结生成失败)"]

        # 2. 溯源匹配 (简单实现：基于关键词匹配)
        summary_objects = []
        
        # 确保 summary_texts 是列表
        if not isinstance(summary_texts, list):
            summary_texts = [str(summary_texts)]

        for text in summary_texts:
            spans = self._find_source_spans(text, chapter.content)
            summary_objects.append(SummarySentence(
                summary_text=text,
                source_spans=spans,
                confidence=1.0 if spans else 0.5
            ))

        # 3. 构建实体对象
        entity_objects = []
        for ent in entities_data:
            try:
                entity_objects.append(Entity(
                    name=ent.get("name", "Unknown"),
                    type=ent.get("type", "Other"),
                    description=ent.get("description", ""),
                    confidence=0.9 # 默认置信度
                ))
            except Exception as e:
                print(f"实体解析失败: {ent}, error: {e}")

        # 4. 构建关系对象
        relationship_objects = []
        for rel in relationships_data:
            try:
                # 显式检查必要字段，因为 .get() 会返回默认空字符串，可能绕过 Pydantic 校验
                # 但如果模型定义为 source: str = Field(...)，传入 "" 是合法的字符串。
                # 然而，空的 source/target/relation 是没有意义的。
                source = rel.get("source", "").strip()
                target = rel.get("target", "").strip()
                relation = rel.get("relation", "").strip()
                description = rel.get("description", "").strip()
                
                if not source or not target or not relation:
                    # 缺少关键信息，跳过
                    continue
                    
                relationship_objects.append(Relationship(
                    source=source,
                    target=target,
                    relation=relation,
                    description=description,
                    confidence=0.9
                ))
            except Exception as e:
                print(f"关系解析失败: {rel}, error: {e}")

        return ChapterSummary(
            chapter_id=chapter.id,
            chapter_title=chapter.title,
            headline=headline,
            summary_sentences=summary_objects,
            entities=entity_objects,
            relationships=relationship_objects
        )

    def _parse_json_response(self, response: str) -> object:
        """解析 LLM 返回的 JSON 字符串"""
        import re
        
        # 1. 移除思维链 <think>...</think>
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        # 2. 尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
            
        # 3. 尝试提取 Markdown 代码块 ```json ... ```
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # 4. 尝试提取最外层的大括号 {}
        # 寻找第一个 { 和最后一个 }
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = cleaned[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"无法解析提取的 JSON 片段: {json_str[:100]}...")
        
        print(f"无法解析 JSON: {cleaned[:200]}...")
        # 降级策略：如果无法解析 JSON，尝试按行分割，并假设每行是一条总结
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        return {
            "headline": lines[0] if lines else None,
            "summary_sentences": lines
        }

    def _find_source_spans(self, summary: str, content: str) -> List[TextSpan]:
        """
        在原文中寻找与总结句最相关的片段。
        采用基于关键词密度的滑动窗口算法。
        """
        # 1. 分词并过滤停用词
        keywords = [w for w in jieba.lcut(summary) if w not in STOPWORDS and len(w) > 1]
        
        if not keywords:
            # 降级：如果找不到关键词，尝试直接搜索前10个字符
            start = content.find(summary[:10])
            if start != -1:
                return [TextSpan(text=content[start:start+len(summary)], start_index=start, end_index=start+len(summary))]
            return []

        # 2. 找到所有关键词在原文中的位置
        # 格式: (index, word)
        keyword_positions = []
        for w in keywords:
            start = 0
            while True:
                idx = content.find(w, start)
                if idx == -1: break
                keyword_positions.append((idx, w))
                start = idx + 1
        
        if not keyword_positions:
            return []

        # 按位置排序
        keyword_positions.sort(key=lambda x: x[0])

        # 3. 滑动窗口寻找最佳匹配区域
        # 窗口大小设定为总结句长度的 2 倍 + 50 字符冗余，确保能覆盖概括性的描述
        window_size = len(summary) * 2 + 50
        
        best_score = 0
        best_span_indices = None # (start, end)
        
        left = 0
        current_keywords_count = defaultdict(int)
        
        for right in range(len(keyword_positions)):
            pos_r, word_r = keyword_positions[right]
            current_keywords_count[word_r] += 1
            
            # 收缩左边界，保证窗口大小不超过限制
            while pos_r - keyword_positions[left][0] > window_size:
                pos_l, word_l = keyword_positions[left]
                current_keywords_count[word_l] -= 1
                if current_keywords_count[word_l] <= 0:
                    del current_keywords_count[word_l]
                left += 1
            
            # 计算得分：唯一关键词的数量
            # (未来可以优化为 TF-IDF 加权)
            score = len(current_keywords_count)
            
            if score > best_score:
                best_score = score
                # 记录当前的跨度
                span_start = keyword_positions[left][0]
                span_end = pos_r + len(word_r)
                best_span_indices = (span_start, span_end)

        # 4. 返回结果
        if best_span_indices:
            start, end = best_span_indices
            # 稍微扩展一点上下文 (前后 5 个字符)，但不要越界
            start = max(0, start - 5)
            end = min(len(content), end + 5)
            
            return [TextSpan(
                text=content[start:end],
                start_index=start,
                end_index=end
            )]
            
        return []
