import re
import os
import argparse
import cn2an

def extract_line_by_match(m, content, type_):
    # 获取匹配内容所在的行的起始和结束位置
    start_index = m.start()
    end_index = m.end()
    
    # 根据匹配位置找到整行
    line_start = content.rfind("\n", 0, start_index) + 1  # 当前行的开始位置
    line_end = content.find("\n", end_index)  # 当前行的结束位置

    if line_end == -1:
        line_end = len(content)
    
    # 提取整行内容
    line_content = content[line_start:line_end].strip()

    # 提取数字部分并转化为阿拉伯数字
    if type_ == "章":
        num = re.search(r'第([零一二三四五六七八九十百千万\d]+)章', line_content)

    if num:
        chinese_num = num.group(1)
        arabic_num = cn2an.cn2an(chinese_num)
        line_content = line_content.replace(chinese_num, str(arabic_num))  # 替换汉字数字为阿拉伯数字

    return line_content

def split_into_chapters(input_file, output_dir='output', encoding='utf-8'):
    """
    只按章节分割，不分卷
    :param input_file: 输入文件路径
    :param output_dir: 输出目录
    :param encoding: 文件编码格式
    """
    try:
        with open(input_file, 'r', encoding=encoding) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件'{input_file}'不存在")
        return
    except UnicodeDecodeError:
        print("错误：文件编码问题，请尝试使用其他编码（如GBK）")
        return

    # 匹配所有以“第X章”开头的章节标题
    chapter_pattern = r'^[第零一二三四五六七八九十百千万\d]+章'  # 章节标题出现在行首
    matches = re.findall(chapter_pattern, content, flags=re.MULTILINE)

    # 查找所有章节位置，过滤掉包含结尾提示的匹配项
    chapter_titles = []
    for m in re.finditer(chapter_pattern, content, re.MULTILINE):
        line = m.group().strip()

        # 判断是否是结尾提示，如果是则跳过
        cleaned_line = re.sub(r'[^\u4e00-\u9fa5]', '', line)  # 去掉非汉字符号
        if cleaned_line.endswith(('终', '完')):
            continue

        chapter_titles.append(extract_line_by_match(m, content, type_="章"))

    if not chapter_titles:
        print(f"未找到任何章节标题，跳过：{input_file}")
        return

    # 收集章节起止位置
    start_positions = [m.start() for m in re.finditer(chapter_pattern, content, re.MULTILINE)]
    total_chapters = len(start_positions)

    # 分割文本内容
    chapters = []

    for i in range(total_chapters):
        start = start_positions[i]
        end = start_positions[i + 1] if i < total_chapters - 1 else len(content)
        chapter_content = content[start:end].strip()

        chapters.append((chapter_titles[i], chapter_content))

    # 保存每一章为独立文件
    for i, (title, content) in enumerate(chapters):
        chapter_filename = os.path.join(output_dir, f"{title}.txt")
        with open(chapter_filename, 'w', encoding=encoding) as chapter_file:
            chapter_file.write(content)
            print(f"已创建章节文件：{chapter_filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='小说章节切割工具')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出目录（默认：input_file文件名）')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码（默认：utf-8）')

    args = parser.parse_args()

    # 如果没有提供输出目录，使用input_file的文件名（去掉扩展名）作为输出目录
    output_dir = args.output if args.output else os.path.splitext(os.path.basename(args.input_file))[0]

    # 如果output目录不存在，则创建它
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"输出目录 '{output_dir}' 已创建。")

    # 调用分章节函数
    split_into_chapters(input_file=args.input_file, output_dir=output_dir, encoding=args.encoding)
