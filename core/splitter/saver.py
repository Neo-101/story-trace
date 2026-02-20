import os
from typing import List
from data_protocol.models import Chapter

def save_chapters(chapters: List[Chapter], output_dir: str, encoding: str = 'utf-8'):
    """
    保存章节列表到文件系统。
    根据是否有 volume_title 来决定是否创建子文件夹。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for chapter in chapters:
        # 确定保存路径
        if chapter.volume_title:
            # 清理非法字符
            volume_clean = "".join([c for c in chapter.volume_title if c not in r'\/:*?"<>|'])
            volume_dir = os.path.join(output_dir, volume_clean)
            if not os.path.exists(volume_dir):
                os.makedirs(volume_dir)
            
            file_path = os.path.join(volume_dir, f"{chapter.title}.txt")
        else:
            file_path = os.path.join(output_dir, f"{chapter.title}.txt")

        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(chapter.content)
            print(f"已保存: {file_path}")
        except Exception as e:
            print(f"保存失败 {file_path}: {e}")
