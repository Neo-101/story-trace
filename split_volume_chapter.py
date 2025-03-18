import re
import os
import argparse

import cn2an

def extract_line_by_match(m, content, type_):
    # 获取匹配内容所在的行的起始和结束位置
    start_index = m.start()
    end_index = m.end()
    
    # 根据匹配位置找到整行
    # 找到当前行的起始位置（上一个换行符之后的位置）和结束位置（下一个换行符之前的位置）
    line_start = content.rfind("\n", 0, start_index) + 1  # 当前行的开始位置
    line_end = content.find("\n", end_index)  # 当前行的结束位置

    # 如果找不到换行符，说明是在最后一行
    if line_end == -1:
        line_end = len(content)
    
    # 提取整行内容
    line_content = content[line_start:line_end].strip()

    # 提取数字部分并转化为阿拉伯数字
    if type_ == "卷":
        num = re.search(r'第([零一二三四五六七八九十百千万\d]+)卷', line_content)
    elif type_ == "章":
        num = re.search(r'第([零一二三四五六七八九十百千万\d]+)章', line_content)

    if num:
        chinese_num = num.group(1)
        arabic_num = cn2an.cn2an(chinese_num)  # 转换汉字数字为阿拉伯数字
        line_content = line_content.replace(chinese_num, str(arabic_num))  # 替换汉字数字为阿拉伯数字

    return line_content

def split_into_chapters(volume_file, volume_folder, encoding='utf-8'):
    """
    将单个分卷的内容按章节分割，并保存在对应文件夹内
    :param volume_file: 分卷txt文件路径
    :param volume_folder: 分卷文件夹路径
    :param encoding: 文件编码格式
    """
    # 读取分卷内容
    try:
        with open(volume_file, 'r', encoding=encoding) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件'{volume_file}'不存在")
        return
    except UnicodeDecodeError:
        print("错误：文件编码问题，请尝试使用其他编码（如GBK）")
        return

    # 匹配所有以“第X章”开头的章节标题
    chapter_pattern = r'^[第零一二三四五六七八九十百千万\d]+章'  # 章节标题出现在行首
    matches = re.findall(chapter_pattern, content, flags=re.MULTILINE)

    # 查找所有分卷位置，过滤掉包含结尾提示的匹配项
    matches = []
    chapter_titles = []
    for m in re.finditer(chapter_pattern, content, re.MULTILINE):  # 使用MULTILINE模式以处理多行
        # 获取匹配到的整行内容
        line = m.group().strip()

        # 判断是否是结尾提示，如果是则跳过
        # 匹配“（第一章《钟楼街的游行》终）”类型的结尾
        cleaned_line = re.sub(r'[^\u4e00-\u9fa5]', '', line)  # 去掉非汉字符号
        if cleaned_line.endswith(('终', '完')):
            continue  # 跳过结尾提示

        # 否则添加到有效的分卷匹配列表
        matches.append(m)

        line_content = extract_line_by_match(m, content, type_="章")

        chapter_titles.append(line_content)

    if not matches:
        print(f"未找到任何章节标题，跳过：{volume_file}")
        return

    # 收集分章起止位置
    start_positions = [m.start() for m in matches]
    total_chapters = len(start_positions)

    # 分割文本内容
    chapters = []  # 存储每一章的内容

    for i in range(total_chapters):
        start = start_positions[i]
        end = start_positions[i + 1] if i < total_chapters - 1 else len(content)

        # 获取当前卷的标题和内容
        chapter_content = content[start:end].strip()

        # 保存卷内容
        chapters.append((chapter_titles[i], chapter_content))


    # 处理每一章并保存为新的文件
    for i, (title, content) in enumerate(chapters):
        # 生成章节文件名
        chapter_filename = os.path.join(volume_folder, f"{title}.txt")

        # 保存章节内容
        with open(chapter_filename, 'w', encoding=encoding) as chapter_file:
            chapter_file.write(content)
            print(f"已创建章节文件：{chapter_filename}")

 

def split_novel_volumes(input_file, output_dir='output', pattern=r'^[第卷\d一二三四五六七八九十百千万]+卷', encoding='utf-8'):
    """
    将小说按卷分割为多个txt文件，并在每个分卷文件夹内执行分章节操作
    :param input_file: 输入文件路径
    :param output_dir: 输出目录
    :param pattern: 匹配分卷的正则表达式（修改为只匹配行首“第X卷”）
    :param encoding: 文件编码
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 使用指定的编码打开文件
        with open(input_file, 'r', encoding=encoding) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件'{input_file}'不存在")
        return
    except UnicodeDecodeError:
        print(f"错误：文件编码问题，无法使用'{encoding}'编码打开文件")
        return

    # 查找所有分卷位置，过滤掉包含结尾提示的匹配项
    matches = []
    volume_titles = []
    for m in re.finditer(pattern, content, re.MULTILINE):  # 使用MULTILINE模式以处理多行
        # 获取匹配到的整行内容
        line = m.group().strip()

        # 判断是否是结尾提示，如果是则跳过
        # 匹配“（第一卷《东林皆石》终）”类型的结尾
        cleaned_line = re.sub(r'[^\u4e00-\u9fa5]', '', line)  # 去掉非汉字符号
        if cleaned_line.endswith(('终', '完')):
            continue  # 跳过结尾提示

        # 否则添加到有效的分卷匹配列表
        matches.append(m)

        line_content = extract_line_by_match(m, content, type_="卷")

        volume_titles.append(line_content)

    if not matches:
        print("未找到任何有效的分卷")
        return

    # 收集分卷起止位置
    start_positions = [m.start() for m in matches]
    total_volumes = len(start_positions)

    # 分割文本内容
    volumes = []  # 存储每一卷的内容

    for i in range(total_volumes):
        start = start_positions[i]
        end = start_positions[i + 1] if i < total_volumes - 1 else len(content)

        # 获取当前卷的标题和内容
        # volume_title = matches[i].group()
        volume_content = content[start:end].strip()

        # 保存卷内容
        volumes.append((volume_titles[i], volume_content))

    # 保存每一卷到独立文件夹中
    for i, (title, content) in enumerate(volumes):
        # 清理文件夹名中的非法字符
        clean_title = re.sub(r'[\\/*?:"<>|]', '_', title)
        volume_folder = os.path.join(output_dir, f"{clean_title}")
        
        # 创建卷文件夹
        os.makedirs(volume_folder, exist_ok=True)
        
        # 保存卷内容到卷文件夹
        volume_filename = os.path.join(volume_folder, f"{clean_title}.txt")
        with open(volume_filename, 'w', encoding=encoding) as f_out:
            f_out.write(content)
            print(f"已创建卷文件：{volume_filename}")

        # 调用分章节函数处理该分卷
        split_into_chapters(volume_filename, volume_folder, encoding)

    print(f"分割完成，共{len(volumes)}个分卷，每个分卷内包含若干章节")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='小说分卷切割工具')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', default='output', help='输出目录（默认：output）')
    parser.add_argument('-p', '--pattern', 
                        default=r'^[第卷\d一二三四五六七八九十百千万]+卷', 
                        help='分卷匹配模式（正则表达式）')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码（默认：utf-8）')

    args = parser.parse_args()
    
    split_novel_volumes(
        input_file=args.input_file,
        output_dir=args.output,
        pattern=args.pattern,
        encoding=args.encoding
    )
