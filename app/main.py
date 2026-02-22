import argparse
import sys
import os
from core.splitter.processor import Splitter
from core.splitter.saver import save_chapters
from core.summarizer.llm_client import ClientFactory
from core.summarizer.generator import SummaryGenerator
from core.utils import calculate_file_hash
from data_protocol.models import Chapter
import json
import time
from core.config import settings
from core.paths import PathManager

def parse_range(range_str: str, max_val: int) -> tuple:
    """
    解析用户输入的范围字符串
    支持格式: 
    - "10" -> (1, 10)
    - "5-15" -> (5, 15)
    - "all" -> (1, max_val)
    - "" (empty) -> (1, max_val)
    """
    s = range_str.strip().lower()
    if not s or s == 'all':
        return (1, max_val)
    
    if '-' in s:
        try:
            start, end = map(int, s.split('-'))
            return (max(1, start), min(max_val, end))
        except ValueError:
            return (1, max_val)
            
    try:
        val = int(s)
        return (1, min(max_val, val))
    except ValueError:
        return (1, max_val)

def get_user_input():
    """交互式获取用户输入"""
    print("\n=== 小说分割工具 ===")
    
    # 0. 尝试加载配置文件
    config_path = "config.json"
    if os.path.exists(config_path):
        print(f"\n检测到配置文件: {config_path}")
        if input("是否加载配置并直接运行? (Y/n): ").strip().lower() != 'n':
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 解析配置
                input_file = config.get('input_file', '')
                encoding = config.get('encoding', 'utf-8')
                output_dir = config.get('output_dir', 'output')
                mode_str = config.get('mode', 'chapter')
                range_str = config.get('chapter_range', '')
                batch_size = config.get('batch_size', 10)
                
                # 映射模式字符串到编号
                mode_map_rev = {'volume': '1', 'chapter': '2', 'batch': '3'}
                mode = mode_map_rev.get(mode_str, '2')
                
                # 解析范围
                # 需要先扫描章节数才能解析 "all" 或 "-10" 吗？
                # parse_range 需要 max_val。
                # 我们可以先扫描文件。
                
                print("\n--- 配置信息 ---")
                print(f"文件: {input_file}")
                print(f"编码: {encoding}")
                print(f"模式: {mode_str}")
                print(f"范围: {range_str if range_str else 'All'}")
                print(f"输出: {output_dir}")
                
                summ_conf = config.get('summarize', {})
                
                # 自动填充 API Key 逻辑 (Fix for .env loading)
                if summ_conf.get('enabled') and summ_conf.get('provider') == 'openrouter':
                    current_key = summ_conf.get('api_key')
                    if not current_key:  # If None or Empty String
                        # 优先从 settings (Pydantic加载的.env) 获取，其次才是 os.getenv
                        env_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
                        if env_key:
                            summ_conf['api_key'] = env_key
                            print(f"  (已自动从 .env/环境变量 加载 OPENROUTER_API_KEY)")

                print(f"AI总结: {'开启' if summ_conf.get('enabled') else '关闭'}")
                if summ_conf.get('enabled'):
                    print(f"  Provider: {summ_conf.get('provider')}")
                    print(f"  Model: {summ_conf.get('model')}")
                
                if input("\n确认执行? (Y/n): ").strip().lower() != 'n':
                    # 执行预扫描以获取章节总数 (用于解析范围)
                    print("\n正在扫描文件结构...")
                    splitter = Splitter(encoding=encoding)
                    content = splitter.read_file(input_file)
                    # 更新为实际检测到的编码
                    encoding = splitter.encoding
                    total_chapters, _, _ = splitter.scan_chapters(content)
                    
                    chapter_range = parse_range(range_str, total_chapters)
                    
                    # 构造返回字典
                    extra_args = {}
                    if mode == '3':
                        extra_args['range'] = batch_size
                    if chapter_range:
                        extra_args['chapter_range'] = chapter_range
                        
                    return {
                        'input_file': input_file,
                        'mode': mode,
                        'output_dir': output_dir,
                        'encoding': encoding,
                        'extra_args': extra_args,
                        'summarize_config': summ_conf
                    }
            except Exception as e:
                print(f"配置文件加载失败: {e}")
                print("将转为手动输入模式...")

    # 1. 获取输入文件
    # 尝试使用 tkinter 弹出文件选择框
    input_file = ""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 隐藏主窗口
        root = tk.Tk()
        root.withdraw()
        
        # 尝试强制窗口置顶 (Windows特定)
        root.attributes('-topmost', True)
        
        print("正在打开文件选择窗口...")
        input_file = filedialog.askopenfilename(
            title="选择小说TXT文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        root.destroy()
    except ImportError:
        # 如果没有 tkinter，静默失败，回退到输入框
        pass
    except Exception as e:
        print(f"无法打开文件选择框 ({e})，请手动输入。")
    
    # 如果用户取消选择或无法使用 tkinter，回退到手动输入
    while not input_file:
        input_file = input("请输入小说txt文件路径: ").strip()
        # 移除可能存在的引号
        input_file = input_file.strip('"').strip("'")
        if os.path.exists(input_file):
            break
        print(f"错误：文件 '{input_file}' 不存在，请重新输入。")
    
    print(f"已选择文件: {input_file}")

    # 2. 编码设置（提前到第二步，以便扫描文件）
    encoding = input("\n请输入文件编码 (默认为 'utf-8', 若乱码可尝试 'gbk'): ").strip()
    if not encoding:
        encoding = 'utf-8'

    # 3. 预扫描章节
    print("\n正在扫描文件结构...")
    try:
        splitter = Splitter(encoding=encoding)
        content = splitter.read_file(input_file)
        # 更新为实际检测到的编码
        encoding = splitter.encoding
        
        total_chapters, titles, is_continuous = splitter.scan_chapters(content)
        
        if total_chapters > 0:
            print(f"✅ 检测到共 {total_chapters} 章。")
            if not is_continuous:
                print("⚠️  警告: 章节编号似乎不连续，建议检查文件内容。")
            else:
                print("   章节编号连续。")
            
            print(f"   首章: {titles[0]}")
            print(f"   末章: {titles[-1]}")
        else:
            print("⚠️  未检测到明显的分章结构 (可能需要按卷或自定义正则)。")
            total_chapters = 999999 # Fallback
            
    except Exception as e:
        print(f"扫描失败: {e}")
        total_chapters = 0

    # 4. 选择处理范围
    chapter_range = None
    if total_chapters > 0:
        range_input = input(f"\n请输入处理范围 (默认处理全部，输入 '10' 代表前10章，'5-20' 代表区间): ").strip()
        chapter_range = parse_range(range_input, total_chapters)
        print(f"已选择范围: 第{chapter_range[0]}章 - 第{chapter_range[1]}章")

    # 5. 选择模式
    print("\n请选择分割模式：")
    print("1. 按卷分割（自动识别分卷，卷内再分章）")
    print("2. 仅按章节分割（整本小说切分为单章文件）")
    print("3. 按数量合并分割（每N章合并为一个文件）")
    
    while True:
        mode = input("请输入模式编号 (1/2/3): ").strip()
        if mode in ['1', '2', '3']:
            break
        print("输入无效，请输入 1, 2 或 3。")

    # 6. 获取输出目录
    output_dir = input(f"\n请输入输出目录 (默认为 '{settings.OUTPUT_DIR.name}'): ").strip()
    if not output_dir:
        output_dir = str(settings.OUTPUT_DIR)

    # 7. 获取特定模式的额外参数
    extra_args = {}
    if mode == '3':
        while True:
            try:
                range_val = input("请输入每个文件包含的章节数 (默认为10): ").strip()
                if not range_val:
                    extra_args['range'] = 10
                else:
                    extra_args['range'] = int(range_val)
                break
            except ValueError:
                print("请输入有效的数字。")
    
    # Pass the scan result range
    if chapter_range:
        extra_args['chapter_range'] = chapter_range

    # 8. AI 总结配置
    summarize_config = {'enabled': False}
    print("\n是否开启 AI 智能总结? (y/N)")
    if input().lower().strip() == 'y':
        summarize_config['enabled'] = True
        
        print("\n请选择 LLM 提供商:")
        print("1. OpenRouter (默认)")
        print("2. Local (Ollama/vLLM)")
        prov_input = input("请输入编号 (1/2): ").strip()
        
        if prov_input == '2':
            summarize_config['provider'] = 'local'
            # 尝试从环境变量获取默认值
            default_base = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
            default_model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:14b")
            
            base_url = input(f"Base URL (默认 '{default_base}'): ").strip()
            summarize_config['base_url'] = base_url if base_url else default_base
            
            model = input(f"Model Name (默认 '{default_model}'): ").strip()
            summarize_config['model'] = model if model else default_model
        else:
            summarize_config['provider'] = 'openrouter'
            # OpenRouter Config
            default_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
            model = input(f"Model Name (默认 '{default_model}'): ").strip()
            summarize_config['model'] = model if model else default_model
            
            # API Key
            env_key = os.getenv("OPENROUTER_API_KEY")
            if env_key:
                print(f"检测到环境变量 OPENROUTER_API_KEY (已隐藏)")
                use_env = input("是否使用环境变量中的 Key? (Y/n): ").strip().lower()
                if use_env == 'n':
                    summarize_config['api_key'] = input("请输入 OpenRouter API Key: ").strip()
                else:
                    summarize_config['api_key'] = env_key
            else:
                summarize_config['api_key'] = input("请输入 OpenRouter API Key: ").strip()

    return {
        'input_file': input_file,
        'mode': mode,
        'output_dir': output_dir,
        'encoding': encoding,
        'extra_args': extra_args,
        'summarize_config': summarize_config
    }

from core.summarizer.prompts import Prompts
from core.cache_manager import CacheManager

def main():
    # 检查是否是启动 Web 服务命令
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        try:
            import uvicorn
            from backend.server import app
            print("=== StoryTrace Visualization Server ===")
            print("正在启动 API 服务...")
            print(f"访问地址: http://{settings.API_HOST}:{settings.API_PORT}/docs")
            uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
        except ImportError:
            print("错误: 请先安装 web 依赖: pip install fastapi uvicorn")
        except Exception as e:
            print(f"启动失败: {e}")
        return

    parser = argparse.ArgumentParser(description='全能小说分割工具')
    parser.add_argument('-i', '--input', help='输入文件路径')
    parser.add_argument('-m', '--mode', choices=['volume', 'chapter', 'batch'], 
                        help='分割模式: volume(按卷), chapter(按章), batch(按数量)')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码')
    parser.add_argument('-r', '--range', type=int, default=10, help='批量分割时的章节数量 (仅batch模式有效)')
    parser.add_argument('--pattern', default=r'^[第卷\d一二三四五六七八九十百千万]+卷', help='分卷匹配模式 (仅volume模式有效)')
    
    # LLM 相关参数
    parser.add_argument('--summarize', action='store_true', help='开启智能总结 (实验性功能)')
    parser.add_argument('--provider', default='openrouter', choices=['local', 'openrouter'], help='LLM 提供商')
    parser.add_argument('--api-key', help='API Key (OpenRouter 需要)')
    parser.add_argument('--model', help='模型名称')
    parser.add_argument('--base-url', help='Local LLM Base URL')

    # 如果没有提供任何参数，且不是被导入调用，则进入交互模式
    if len(sys.argv) == 1:
        args_dict = get_user_input()
        print("\nDEBUG: 用户输入接收完成，正在初始化...", flush=True)
        input_file = args_dict['input_file']
        mode = args_dict['mode']
        output_dir = args_dict['output_dir']
        encoding = args_dict['encoding']
        
        # 映射模式编号到内部名称
        mode_map = {'1': 'volume', '2': 'chapter', '3': 'batch'}
        mode_name = mode_map[mode]
        
        extra_args = args_dict['extra_args']
        batch_size = extra_args.get('range', 10)
        chapter_range_filter = extra_args.get('chapter_range')
        
        pattern = r'^[第卷\d一二三四五六七八九十百千万]+卷' # 交互模式使用默认pattern
        
        # 读取交互模式下的 LLM 配置
        summarize_config = args_dict.get('summarize_config', {'enabled': False})
        summarize = summarize_config['enabled']
        provider = summarize_config.get('provider', 'openrouter')
        api_key = summarize_config.get('api_key')
        model = summarize_config.get('model')
        base_url = summarize_config.get('base_url')
        
        # 如果 Config 中没有提供 API Key，尝试从环境变量获取
        if not api_key and provider == 'openrouter':
            api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
            if api_key:
                print("DEBUG: 使用 .env/环境变量 中的 OPENROUTER_API_KEY")
    else:
        args = parser.parse_args()
        if not args.input:
            parser.error("非交互模式下必须指定输入文件 (-i/--input)")
        if not args.mode:
            parser.error("非交互模式下必须指定模式 (-m/--mode)")
            
        input_file = args.input
        mode_name = args.mode
        output_dir = args.output if args.output else str(settings.OUTPUT_DIR)
        encoding = args.encoding
        batch_size = args.range
        pattern = args.pattern
        chapter_range_filter = None # CLI模式暂不支持 range filter，后续可添加
        
        summarize = args.summarize
        provider = args.provider
        
        # 优先从命令行参数获取，如果没有，则尝试从环境变量获取
        api_key = args.api_key or settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        model = args.model
        base_url = args.base_url

        # 如果是 OpenRouter 且没有指定 Model，尝试从环境变量获取默认 Model
        if provider == 'openrouter' and not model:
             model = settings.OPENROUTER_MODEL or os.getenv("OPENROUTER_MODEL")
             
        # 如果是 Local 且没有指定参数，尝试从环境变量获取
        if provider == 'local':
             if not base_url:
                 base_url = settings.LOCAL_LLM_BASE_URL or os.getenv("LOCAL_LLM_BASE_URL")
             if not model:
                 model = settings.LOCAL_LLM_MODEL or os.getenv("LOCAL_LLM_MODEL")

    # 构建最终输出目录结构
    # 1. 获取小说名（输入文件名，不含扩展名）
    novel_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # --- 自动复制外部文件逻辑 ---
    # 获取项目根目录 (假设 main.py 在 app/ 目录下)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_abs = os.path.abspath(input_file)
    
    # 检查文件是否在项目目录内
    if not input_abs.startswith(project_root):
        print(f"\n提示: 检测到输入文件位于项目目录外 ({input_abs})")
        inputs_dir = os.path.join(project_root, "inputs")
        os.makedirs(inputs_dir, exist_ok=True)
        
        new_path = os.path.join(inputs_dir, os.path.basename(input_file))
        
        # 自动复制
        try:
            import shutil
            if not os.path.exists(new_path):
                print(f"正在复制文件到项目目录: {new_path} ...")
                shutil.copy2(input_file, new_path)
            else:
                print(f"项目目录内已存在同名文件，将使用: {new_path}")
            
            # 更新 input_file 指向新路径
            input_file = new_path
        except Exception as e:
            print(f"警告: 文件复制失败 ({e})，将继续使用原路径。")

    print(f"DEBUG: 正在计算文件哈希... (文件: {input_file})", flush=True)
    # 2. 计算文件哈希（取前8位即可）
    file_hash = calculate_file_hash(input_file)
    if len(file_hash) > 8:
        file_hash = file_hash[:8]
    print(f"DEBUG: 文件哈希: {file_hash}", flush=True)
    
    # --- 缓存检查逻辑 (v3.0) ---
    print(f"DEBUG: Summarize={summarize}, Provider={provider}", flush=True)
    
    # 1. 计算当前运行的 Fingerprint
    # 注意：这里我们还没有加载 prompts，需要引入 Prompts 类来计算
    current_fingerprint = {
        "source_file_hash": file_hash,
        "prompt_hash": Prompts.get_prompt_hash() if summarize else None,
        "model_config": {
            "provider": provider,
            "model": model,
            # "temperature": ... (如果后续支持 temp 参数，这里也要加上)
        } if summarize else None,
        "splitter_config": {
            "mode": mode_name,
            "batch_size": batch_size if mode_name == 'batch' else None,
            "chapter_range_filter": chapter_range_filter, # 新增范围过滤指纹
            "pattern": pattern if mode_name == 'volume' else None
        }
    }
    print("DEBUG: 指纹计算完成，正在检查缓存...")
    
    # 2. 扫描历史记录
    novel_output_root = PathManager.get_novel_root(novel_name, file_hash)
    cache_hit_path = None
    cache_hit_timestamp = None
    
    if os.path.exists(novel_output_root) and summarize: # 只有开启总结时才值得缓存
        for ts in os.listdir(novel_output_root):
            ts_path = os.path.join(novel_output_root, ts)
            meta_path = os.path.join(ts_path, "run_metadata.json")
            if os.path.isdir(ts_path) and os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        # 比较指纹
                        # 注意：旧版本的 metadata 没有 fingerprint 字段，会自动忽略
                        if meta.get("fingerprint") == current_fingerprint:
                            cache_hit_path = ts_path
                            cache_hit_timestamp = ts
                            break
                except Exception:
                    continue
    
    # 3. 如果命中缓存
    if cache_hit_path:
        print(f"\n[Cache Hit] 发现完全相同的历史运行记录: {cache_hit_timestamp}")
        print(f"无需重复调用 LLM。")
        
        # 生成新的时间戳目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        final_output_dir = PathManager.get_run_dir(novel_name, file_hash, timestamp)
        os.makedirs(final_output_dir, exist_ok=True)
        
        # 创建 ref_link.json
        link_data = {
            "link_type": "cache_hit",
            "target_timestamp": cache_hit_timestamp,
            "reason": "Fingerprint match",
            "fingerprint": current_fingerprint
        }
        with open(os.path.join(final_output_dir, "ref_link.json"), 'w', encoding='utf-8') as f:
            json.dump(link_data, f, ensure_ascii=False, indent=2)
            
        print(f"已创建链接目录: {final_output_dir}")
        print(f"您可以在 Visualization Server 中查看此记录（将自动指向历史数据）。")
        return
    
    # --- 缓存检查结束 ---

    # 3. 获取当前时间戳
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # 最终路径：output_dir/novel_name/file_hash/timestamp
    final_output_dir = PathManager.get_run_dir(novel_name, file_hash, timestamp)
    abs_final_output_dir = os.path.abspath(final_output_dir)
    
    # 执行分割逻辑
    print(f"\n开始处理：{input_file}")
    print(f"模式：{mode_name}")
    print(f"输出目录 (绝对路径)：{abs_final_output_dir}")
    
    try:
        print(f"正在读取文件 (编码: {encoding})...")
        splitter = Splitter(encoding=encoding)
        content = splitter.read_file(input_file)
        
        print("正在分割章节...")
        if mode_name == 'volume':
            # 暂时不支持卷模式的范围过滤
            chapters = splitter.split_by_volume(content, volume_pattern=pattern)
        elif mode_name == 'chapter':
            chapters = splitter.split_by_chapter(content, chapter_range=chapter_range_filter)
        elif mode_name == 'batch':
            chapters = splitter.split_by_batch(content, batch_size=batch_size, chapter_range=chapter_range_filter)
        else:
            print(f"不支持的模式: {mode_name}")
            return
            
        if chapters:
            print(f"成功分割出 {len(chapters)} 章。正在保存...")
            # 使用新的 final_output_dir 保存章节
            # 强制使用 UTF-8 保存，确保 Web UI 能正确读取
            save_chapters(chapters, final_output_dir, encoding='utf-8')
            print("\n分割处理完成！")
            
            # 如果开启了总结功能
            if summarize:
                print("\n=== 开始智能总结 ===")
                try:
                    # 确保参数不为空
                    client_kwargs = {
                        "provider": provider,
                        "api_key": api_key,
                        "model": model,
                        "base_url": base_url
                    }
                    # 过滤掉 None 值和空字符串
                    client_kwargs = {k: v for k, v in client_kwargs.items() if v}
                    
                    llm_client = ClientFactory.create_client(**client_kwargs)
                    generator = SummaryGenerator(llm_client)
                    
                    # --- v4.0 Chapter-Level Caching ---
                    # Initialize CacheManager
                    cache_dir = PathManager.get_cache_dir()
                    cache_manager = CacheManager(str(cache_dir))
                    
                    prompt_hash = Prompts.get_prompt_hash()
                    model_config = {
                        "provider": provider,
                        "model": model,
                        "base_url": base_url
                    }
                    
                    import asyncio
                    
                    # Initialize total_chapters before defining async functions
                    total_chapters = len(chapters)

                    async def process_chapter_async(i, ch, cache_manager, generator, prompt_hash, model_config, semaphore, file_lock, jsonl_path):
                        async with semaphore:
                            print(f"[{i+1}/{total_chapters}] 处理章节: {ch.title} ... ", end="", flush=True)
                            
                            # 1. Try Cache
                            cached_summary = cache_manager.get_cached_summary(ch.content, prompt_hash, model_config)
                            
                            summary_data = None
                            
                            if cached_summary:
                                print("✅ 命中缓存")
                                cached_summary.chapter_id = ch.id 
                                summary_data = cached_summary.model_dump()
                            else:
                                # 2. Generate (Async) with Retry
                                max_retries = 3
                                retry_delay = 2
                                
                                for attempt in range(max_retries):
                                    try:
                                        summary = await generator.generate_summary_async(ch)
                                        
                                        # 3. Save to Cache
                                        try:
                                            cache_manager.save_summary(ch.content, prompt_hash, model_config, summary)
                                        except Exception as cache_err:
                                            print(f"(Cache Write Failed: {cache_err}) ", end="")
                                            
                                        summary_data = summary.model_dump()
                                        print("✨ 生成完成")
                                        break # Success
                                    except Exception as e:
                                        if attempt < max_retries - 1:
                                            print(f"⚠️ 失败(重试 {attempt+1}/{max_retries}): {e} ... ", end="", flush=True)
                                            await asyncio.sleep(retry_delay * (2 ** attempt)) # Exponential backoff
                                        else:
                                            print(f"❌ 最终失败: {e}")
                                            # Create Empty Placeholder to keep chapter in timeline
                                            from data_protocol.models import ChapterSummary
                                            empty_summary = ChapterSummary(
                                                chapter_id=ch.id,
                                                chapter_title=ch.title,
                                                headline="生成失败",
                                                summary_sentences=[],
                                                entities=[],
                                                relationships=[]
                                            )
                                            summary_data = empty_summary.model_dump()
                                
                            # Real-time save to summaries.jsonl (with lock)
                            if summary_data:
                                async with file_lock:
                                    with open(jsonl_path, 'a', encoding='utf-8') as f:
                                        json.dump(summary_data, f, ensure_ascii=False)
                                        f.write('\n')
                            
                            return (i, summary_data)

                    async def run_batch_processing():
                        # Adjust concurrency based on provider
                        limit = 1 if provider == 'local' else 5
                        semaphore = asyncio.Semaphore(limit)
                        file_lock = asyncio.Lock()
                        jsonl_path = os.path.join(final_output_dir, "summaries.jsonl")
                        
                        tasks = []
                        for i, ch in enumerate(chapters):
                            task = process_chapter_async(i, ch, cache_manager, generator, prompt_hash, model_config, semaphore, file_lock, jsonl_path)
                            tasks.append(task)
                        
                        results = await asyncio.gather(*tasks)
                        
                        # Sort results by index to ensure order
                        valid_results = [r for r in results if r is not None]
                        valid_results.sort(key=lambda x: x[0])
                        
                        return [r[1] for r in valid_results]

                    # Run Async Loop
                    summaries = asyncio.run(run_batch_processing())
                    
                    # 保存总结结果，直接保存在 final_output_dir 根目录
                    summary_path = os.path.join(final_output_dir, "summaries.json")
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        json.dump(summaries, f, ensure_ascii=False, indent=2)
                    print(f"总结已保存至: {summary_path}")
                    
                    # 同时保存一份 metadata，记录这次运行的参数
                    metadata = {
                        "timestamp": timestamp,
                        "novel_name": novel_name,
                        "file_hash": file_hash,
                        "input_file": os.path.abspath(input_file),
                        "provider": provider,
                        "model": model,
                        "chapter_count": len(summaries),
                        "fingerprint": current_fingerprint # 记录指纹，供下次校验
                    }
                    with open(os.path.join(final_output_dir, "run_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    # --- 自动执行数据库迁移 (Auto Migration) ---
                    print("\n=== 正在自动更新图谱数据库 ===")
                    try:
                        from scripts.migrate_json_to_sqlite import migrate
                        print("正在同步数据到 storytrace.db ...")
                        migrate()
                        print("✅ 数据库同步完成！现在可以启动 Web 服务查看图谱了。")
                    except Exception as me:
                        print(f"⚠️ 自动迁移失败: {me}")
                        print("请稍后手动运行: python scripts/migrate_json_to_sqlite.py")

                except Exception as e:
                    print(f"智能总结失败: {e}")
                    import traceback
                    traceback.print_exc()
            
        else:
            print("\n未找到任何章节。")
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
