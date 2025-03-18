import re
import os
import argparse
import cn2an

def extract_line_by_match(m, content):
    start_index = m.start()
    end_index = m.end()
    line_start = content.rfind("\n", 0, start_index) + 1
    line_end = content.find("\n", end_index)
    if line_end == -1:
        line_end = len(content)
    line_content = content[line_start:line_end].strip()
    num = re.search(r'第([零一二三四五六七八九十百千万\d]+)章', line_content)
    if num:
        chinese_num = num.group(1)
        arabic_num = cn2an.cn2an(chinese_num)
        line_content = line_content.replace(chinese_num, str(arabic_num))
    return line_content

def split_into_chapters(input_file, output_dir='output', encoding='utf-8', chapter_range=10):
    try:
        with open(input_file, 'r', encoding=encoding) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件'{input_file}'不存在")
        return
    except UnicodeDecodeError:
        print("错误：文件编码问题，请尝试使用其他编码（如GBK）")
        return
    
    chapter_pattern = r'^[第零一二三四五六七八九十百千万\d]+章'
    matches = re.finditer(chapter_pattern, content, re.MULTILINE)
    
    chapter_titles = []
    start_positions = []
    for m in matches:
        chapter_titles.append(extract_line_by_match(m, content))
        start_positions.append(m.start())
    
    if not chapter_titles:
        print(f"未找到任何章节标题，跳过：{input_file}")
        return
    
    total_chapters = len(start_positions)
    chapters = []
    for i in range(total_chapters):
        start = start_positions[i]
        end = start_positions[i + 1] if i < total_chapters - 1 else len(content)
        chapters.append((chapter_titles[i], content[start:end].strip()))
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"输出目录 '{output_dir}' 已创建。")
    
    for i in range(0, total_chapters, chapter_range):
        start_chapter = i + 1
        end_chapter = min(i + chapter_range, total_chapters)
        combined_content = "\n\n".join(ch[1] for ch in chapters[i:end_chapter])
        output_filename = os.path.join(output_dir, f"{start_chapter}-{end_chapter}.txt")
        with open(output_filename, 'w', encoding=encoding) as out_file:
            out_file.write(combined_content)
            print(f"已创建章节文件：{output_filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='小说章节批量切割工具')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出目录（默认：input_file文件名）')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码（默认：utf-8）')
    parser.add_argument('-r', '--range', type=int, default=10, help='每个txt包含的章节数（默认：10）')
    
    args = parser.parse_args()
    output_dir = args.output if args.output else os.path.splitext(os.path.basename(args.input_file))[0]
    split_into_chapters(input_file=args.input_file, output_dir=output_dir, encoding=args.encoding, chapter_range=args.range)
