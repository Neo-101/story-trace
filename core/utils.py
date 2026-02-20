import re
import hashlib
import cn2an

def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件的哈希值。
    
    :param file_path: 文件路径
    :param algorithm: 哈希算法 ('md5', 'sha1', 'sha256' 等)
    :return: 十六进制哈希字符串
    """
    hash_obj = hashlib.new(algorithm)
    # 分块读取文件以支持大文件
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except FileNotFoundError:
        return "unknown_hash"

def extract_line_by_match(match, content, match_type):
    """
    根据正则匹配结果提取整行内容，并将中文数字转换为阿拉伯数字。
    
    :param match: re.Match 对象
    :param content: 完整文本内容
    :param match_type: 匹配类型，支持 "卷" 或 "章"
    :return: 处理后的标题行内容（包含阿拉伯数字）
    """
    # 获取匹配内容所在的行的起始和结束位置
    start_index = match.start()
    end_index = match.end()
    
    # 找到当前行的起始位置（上一个换行符之后）和结束位置（下一个换行符之前）
    line_start = content.rfind("\n", 0, start_index) + 1
    line_end = content.find("\n", end_index)
    
    # 如果找不到换行符，说明是在最后一行
    if line_end == -1:
        line_end = len(content)
    
    # 提取整行内容
    line_content = content[line_start:line_end].strip()
    
    # 提取数字部分并转化为阿拉伯数字
    num_match = None
    if match_type == "卷":
        num_match = re.search(r'第([零一二三四五六七八九十百千万\d]+)卷', line_content)
    elif match_type == "章":
        num_match = re.search(r'第([零一二三四五六七八九十百千万\d]+)章', line_content)
    
    if num_match:
        chinese_num = num_match.group(1)
        try:
            # 尝试转换中文数字为阿拉伯数字
            arabic_num = cn2an.cn2an(chinese_num)
            line_content = line_content.replace(chinese_num, str(arabic_num))
        except ValueError:
            # 如果转换失败（例如混合数字），则保留原样或进行部分处理
            pass

    return line_content
