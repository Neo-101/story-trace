import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.summarizer.generator import SummaryGenerator
from data_protocol.models import TextSpan

class TestSourceSpan(unittest.TestCase):
    def setUp(self):
        # Mock LLM client (not needed for this test)
        self.generator = SummaryGenerator(None)
        
        # 构造一段较长的模拟小说文本 (模拟约 500 字)
        self.long_content = (
            "第一章 序幕\n"
            "天空阴沉沉的，仿佛要压下来一般。李云站在悬崖边，看着脚下翻滚的云海，心中充满了迷茫。"
            "他本是青云门的一名普通弟子，因为一次意外，获得了一块神秘的玉佩。这块玉佩通体温润，"
            "上面刻着古老的符文，似乎隐藏着巨大的秘密。\n"
            "“你真的决定要跳下去吗？”一个苍老的声音在他身后响起。\n"
            "李云猛地回头，只见一位身穿灰袍的老者正注视着他。老者的眼神深邃如海，仿佛能看穿人心。"
            "“如果不跳，我也逃不过他们的追杀。”李云咬紧牙关，眼中闪过一丝决绝。\n"
            "老者叹了口气，摇了摇头：“跳下去或许有一线生机，但也可能是万劫不复。这玉佩既是机缘，也是祸根。”\n"
            "李云紧紧握住手中的玉佩，感受着它传来的微弱热流。他知道，自己已经没有退路了。"
            "身后的追兵越来越近，嘈杂的脚步声和叫喊声清晰可闻。\n"
            "“拼了！”李云大喝一声，纵身一跃，跳入了茫茫云海之中。\n"
            "风声在耳边呼啸，失重感瞬间袭来。就在他以为自己必死无疑时，怀中的玉佩突然爆发出一道耀眼的光芒，"
            "将他整个人包裹其中。光芒散去，李云的身影已消失不见，只剩下悬崖边老者意味深长的目光。"
        )

    def test_exact_match(self):
        """测试完全匹配的情况"""
        summary = "李云站在悬崖边，看着脚下翻滚的云海"
        spans = self.generator._find_source_spans(summary, self.long_content)
        self.assertTrue(spans, "应该找到匹配")
        self.assertIn("李云站在悬崖边", spans[0].text)
        print(f"\n[Exact Match]\nSummary: {summary}\nFound: {spans[0].text}")

    def test_fuzzy_match_summary(self):
        """测试 LLM 概括性总结 (关键词匹配)"""
        # 总结提取了关键词：李云、玉佩、老者、追杀、跳入云海
        summary = "李云被追杀至悬崖边，在神秘老者的注视下，带着玉佩跳入云海逃生。"
        
        spans = self.generator._find_source_spans(summary, self.long_content)
        
        self.assertTrue(spans, "应该找到匹配")
        # 验证找到的片段是否包含核心情节
        found_text = spans[0].text
        print(f"\n[Fuzzy Match]\nSummary: {summary}\nFound: {found_text}")
        
        # 只要能定位到包含"跳入"、"云海"、"老者"等关键词的密集区域即可
        # 算法应该定位到最后一段或倒数第二段
        self.assertTrue(any(k in found_text for k in ["跳入", "云海", "老者", "玉佩"]), "片段应包含关键词")

    def test_short_summary_long_distance(self):
        """测试关键词跨度较大的情况"""
        summary = "老者感叹玉佩是祸根"
        spans = self.generator._find_source_spans(summary, self.long_content)
        self.assertTrue(spans)
        print(f"\n[Long Distance]\nSummary: {summary}\nFound: {spans[0].text}")
        self.assertIn("祸根", spans[0].text)

    def test_no_match(self):
        """测试完全无关的内容"""
        summary = "哈利波特骑着扫帚飞走了"
        spans = self.generator._find_source_spans(summary, self.long_content)
        self.assertFalse(spans, "不应找到匹配")

if __name__ == "__main__":
    unittest.main()
