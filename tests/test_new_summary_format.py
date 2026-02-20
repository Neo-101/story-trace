import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.summarizer.generator import SummaryGenerator
from data_protocol.models import Chapter

class TestSummaryGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.generator = SummaryGenerator(self.mock_llm)
        self.chapter = Chapter(
            id="test_ch",
            title="测试章节",
            content="这里是测试内容。",
            word_count=10
        )

    def test_parse_new_format(self):
        """测试新的 JSON 对象格式"""
        json_response = """
        {
            "headline": "这是一个测试标题",
            "summary_sentences": [
                "第一句总结",
                "第二句总结"
            ]
        }
        """
        self.mock_llm.chat_completion.return_value = json_response
        
        summary = self.generator.generate_summary(self.chapter)
        
        self.assertEqual(summary.headline, "这是一个测试标题")
        self.assertEqual(len(summary.summary_sentences), 2)
        self.assertEqual(summary.summary_sentences[0].summary_text, "第一句总结")

    def test_parse_old_format(self):
        """测试旧的 JSON 列表格式 (兼容性)"""
        json_response = """
        [
            "旧格式总结1",
            "旧格式总结2"
        ]
        """
        self.mock_llm.chat_completion.return_value = json_response
        
        summary = self.generator.generate_summary(self.chapter)
        
        # 此时 headline 应该 fallback 到第一句
        self.assertEqual(summary.headline, "旧格式总结1")
        self.assertEqual(len(summary.summary_sentences), 2)

    def test_parse_invalid_json(self):
        """测试无效 JSON 的降级处理"""
        raw_text = """
        非 JSON 内容
        第二行
        """
        self.mock_llm.chat_completion.return_value = raw_text
        
        summary = self.generator.generate_summary(self.chapter)
        
        self.assertEqual(summary.headline, "非 JSON 内容")
        self.assertEqual(len(summary.summary_sentences), 2)

if __name__ == "__main__":
    unittest.main()
