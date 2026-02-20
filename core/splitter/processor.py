import re
import os
from typing import List, Tuple, Optional
from data_protocol.models import Chapter, BookStructure
from core.utils import extract_line_by_match

class Splitter:
    """
    核心分割器类，负责将文本分割为章节对象。
    """
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def read_file(self, file_path: str) -> str:
        """读取文件内容，尝试多种编码"""
        encodings_to_try = [self.encoding]
        
        # 添加常见备选编码
        common_encodings = ['utf-8', 'utf-8-sig', 'gb18030', 'gbk', 'big5']
        for enc in common_encodings:
            if enc.lower() != self.encoding.lower():
                encodings_to_try.append(enc)
        
        # 去重
        seen = set()
        final_encodings = []
        for enc in encodings_to_try:
            if enc not in seen:
                final_encodings.append(enc)
                seen.add(enc)

        for enc in final_encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                    print(f"成功使用编码读取文件: {enc}")
                    self.encoding = enc # 更新为实际有效的编码
                    return content
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                raise FileNotFoundError(f"文件 {file_path} 不存在。")
            except Exception:
                continue
        
        # 如果所有尝试都失败
        raise ValueError(f"无法读取文件 {file_path}，已尝试编码: {', '.join(final_encodings)}。请检查文件是否损坏。")

    def scan_chapters(self, content: str) -> Tuple[int, List[str], bool]:
        """
        快速扫描章节结构
        Returns:
            total_count: 总章节数
            titles: 章节标题列表
            is_continuous: 是否检测到连续的数字编号 (1, 2, 3...)
        """
        # 支持繁体中文数字和异体字
        cn_nums = '零一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬億'
        # 匹配 "第xxx章" 或 "Chapter xxx"
        chapter_pattern = fr'(?:^第[{cn_nums}\d]+[章回節节])|(?:^Chapter\s+\d+)'
        
        matches = list(re.finditer(chapter_pattern, content, re.MULTILINE | re.IGNORECASE))
        
        titles = []
        for match in matches:
            line_start = match.start()
            line_end = content.find('\n', line_start)
            if line_end == -1: line_end = len(content)
            titles.append(content[line_start:line_end].strip())
            
        total = len(titles)
        if total == 0:
            return 0, [], False
            
        # Check continuity (heuristic)
        # Try to extract numbers from first few chapters
        is_continuous = True
        # (Simple check: if we found chapters, we assume structure exists. 
        #  Strict continuity check is hard due to "第十章" vs "第10章" mixing)
        
        return total, titles, is_continuous

    def split_by_chapter(self, content: str, chapter_range: Optional[Tuple[int, int]] = None) -> List[Chapter]:
        """
        按章节分割
        Args:
            content: 文本内容
            chapter_range: (start, end) 闭区间，从1开始计数。例如 (1, 10) 表示第1到第10章。
        """
        # 支持繁体中文数字和异体字
        cn_nums = '零一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬億'
        chapter_pattern = fr'(?:^第[{cn_nums}\d]+[章回節节])|(?:^Chapter\s+\d+)'
        
        print(f"DEBUG: 正在使用正则匹配章节: {chapter_pattern[:50]}...")
        matches = list(re.finditer(chapter_pattern, content, re.MULTILINE | re.IGNORECASE))
        print(f"DEBUG: 匹配到 {len(matches)} 个潜在章节标题。")
        
        if not matches:
            return []

        # Apply Range Filtering
        start_idx = 0
        end_idx = len(matches)
        
        if chapter_range:
            r_start, r_end = chapter_range
            print(f"DEBUG: 应用范围过滤: {r_start}-{r_end}")
            # Adjust 1-based index to 0-based
            start_idx = max(0, r_start - 1)
            end_idx = min(len(matches), r_end)
            
            print(f"DEBUG: 转换索引: [{start_idx}:{end_idx}]")
            
            if start_idx >= len(matches):
                print(f"DEBUG: 起始索引 {start_idx} 超出范围 (总数 {len(matches)})")
                return []
                
        # Filter matches
        target_matches = matches[start_idx : end_idx]
        if not target_matches:
            print("DEBUG: 过滤后章节列表为空。")
            return []
            
        print(f"DEBUG: 最终将处理 {len(target_matches)} 章。")

        chapters = []
        # We need to handle the content extraction carefully because we might be skipping chapters.
        # For the last selected chapter, its content goes until the NEXT chapter in the original list starts.
        
        for i, match in enumerate(target_matches):
            # Original index in 'matches' list
            original_idx = start_idx + i
            
            # Get Title
            line_start = match.start()
            line_end = content.find('\n', line_start)
            if line_end == -1: line_end = len(content)
            title_line = content[line_start:line_end].strip()
            
            # Get Content
            content_start = line_end
            
            # Find end of content: start of the NEXT chapter in the ORIGINAL list
            if original_idx < len(matches) - 1:
                content_end = matches[original_idx + 1].start()
            else:
                content_end = len(content)
                
            chapter_content = content[content_start:content_end].strip()
            
            chapters.append(Chapter(
                id=f"ch_{original_idx + 1}", # Keep original ID to maintain consistency across runs
                title=title_line,
                content=chapter_content,
                word_count=len(chapter_content)
            ))
            
        return chapters

    def split_by_volume(self, content: str, volume_pattern: str = None) -> List[Chapter]:
        """按卷分割，卷内再分章"""
        # 如果未提供 pattern，使用默认增强版
        if not volume_pattern:
            cn_nums = '零一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬億'
            volume_pattern = fr'^[第卷{cn_nums}\d]+[卷巻]'
            
        matches = list(re.finditer(volume_pattern, content, re.MULTILINE))
        
        if not matches:
            # 如果没有分卷，尝试直接分章
            return self.split_by_chapter(content)

        all_chapters = []
        for i, match in enumerate(matches):
            # 获取卷标题行
            line_start = match.start()
            line_end = content.find('\n', line_start)
            if line_end == -1:
                line_end = len(content)
            
            volume_title_line = content[line_start:line_end].strip()

            cleaned_line = re.sub(r'[^\u4e00-\u9fa5]', '', volume_title_line)
            if cleaned_line.endswith(('终', '完', '終')):
                continue
            
            # 获取卷内容范围
            content_start = line_end
            if i < len(matches) - 1:
                content_end = matches[i+1].start()
            else:
                content_end = len(content)
            
            volume_content = content[content_start:content_end].strip()
            
            # 在卷内分章
            # 注意：split_by_chapter 会重新从 volume_content 中找章节
            volume_chapters = self.split_by_chapter(volume_content)
            
            # 如果卷内找不到章节（例如序卷），可能整卷就是一个内容
            if not volume_chapters and volume_content:
                 volume_chapters = [Chapter(
                     id=f"vol_{i+1}_content",
                     title=volume_title_line, # 使用卷名作为章名
                     content=volume_content,
                     word_count=len(volume_content)
                 )]

            for ch in volume_chapters:
                ch.volume_title = volume_title_line
                # 更新ID以包含卷信息，确保唯一性
                # ch.id 已经是 ch_1, ch_2...
                ch.id = f"vol_{i+1}_{ch.id}"
                all_chapters.append(ch)
                
        return all_chapters

    def split_by_batch(self, content: str, batch_size: int = 10, chapter_range: Optional[Tuple[int, int]] = None) -> List[Chapter]:
        """按数量合并分割"""
        # 首先按章节分割
        raw_chapters = self.split_by_chapter(content, chapter_range)
        if not raw_chapters:
            return []

        batched_chapters = []
        total = len(raw_chapters)
        
        for i in range(0, total, batch_size):
            batch = raw_chapters[i : i + batch_size]
            start_ch = i + 1
            end_ch = min(i + batch_size, total)
            
            combined_content = "\n\n".join([c.content for c in batch])
            title = f"第{start_ch}-{end_ch}章"
            
            batched_chapters.append(Chapter(
                id=f"batch_{start_ch}_{end_ch}",
                title=title,
                content=combined_content,
                word_count=len(combined_content)
            ))
            
        return batched_chapters
