"""
Author: HappyDIY
Use this module
(You should install them on "python -m pip"):
requests
tqdm
Use this command to start translate:
python script.py file_dir -t translate_language (Optional)
"""
import re
import os
import argparse
import time
import requests
from tqdm import tqdm

def extract_translatable(text):
    """分离 §符号格式 和 可翻译文本（保留格式符号）"""
    # 使用正则表达式匹配所有 §符号+字符 和非§部分
    parts = re.split(r'(§.)', text)
    return parts

def translate_parts(parts, dest='zh-CN'):
    """只翻译非§符号的部分"""
    translated_parts = []
    for part in parts:
        if re.match(r'§.', part):
            # 保留格式符号
            translated_parts.append(part)
        else:
            # 翻译文本部分
            if part.strip():
                translated = translate_text(part, dest)
                translated_parts.append(translated)
            else:
                translated_parts.append(part)
    return ''.join(translated_parts)

def translate_text(text, dest='zh-CN', max_retries=3):
    """翻译函数（保留原文中的特殊符号）"""
    url = "https://translate.googleapis.com/translate_a/single"
    
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": dest,
        "dt": "t",
        "q": text
    }
    
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://translate.google.com/"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, proxies=proxies, headers=headers, timeout=15)
            response.raise_for_status()
            translated = response.json()[0][0][0]
            return translated
        except requests.exceptions.HTTPError as e:
            status = response.status_code
            print(f"HTTP错误 ({status}): {e}")
            if status == 429:
                wait_time = 10 * (attempt + 1)
                print(f"等待{wait_time}秒...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"异常: {str(e)}")
        time.sleep(2)
    return text

def generate_output_path(input_path):
    """生成输出文件路径"""
    dir_name = os.path.dirname(input_path)
    base_name = os.path.basename(input_path)
    name, ext = os.path.splitext(base_name)
    return os.path.join(dir_name, f"{name}_translate{ext}")

def main(input_file, target_lang='zh-CN'):
    output_file = generate_output_path(input_file)
    
    print(f"\n{'='*40}")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"目标语言: {target_lang}")
    print(f"代理地址: http://127.0.0.1:7890")
    print(f"{'='*40}\n")

    # 文件读取
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print("检测到非UTF-8编码，尝试GBK编码...")
        with open(input_file, 'r', encoding='gbk') as f:
            lines = f.readlines()

    processed = []
    total_lines = len(lines)
    
    with tqdm(total=total_lines, desc="翻译进度", unit="line", ncols=100) as pbar:
        for idx, line in enumerate(lines, 1):
            original_line = line.strip()
            
            # 跳过注释和空行
            if not original_line or original_line.startswith('#'):
                processed.append(line)
                pbar.update(1)
                continue
                
            # 处理键值对
            if '=' in original_line:
                key, value = original_line.split('=', 1)
                # 分离并处理可翻译部分
                parts = extract_translatable(value.strip())
                translated_value = translate_parts(parts, target_lang)
                new_line = f"{key}={translated_value}\n"
                
                # 打印日志
                print(f"\n[原始] {value.strip()}")
                print(f"[翻译] {translated_value}")
            else:
                new_line = line
            
            processed.append(new_line)
            pbar.update(1)
            time.sleep(0.5)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(processed)
    
    print("\n" + "="*40)
    print(f"✅ 翻译完成！共处理 {total_lines} 行")
    print(f"生成文件: {output_file}")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Minecraft Mod 翻译工具 (保留§格式版)',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('input', help='输入文件路径（例如：en_us.lang）')
    parser.add_argument('-t', '--target', default='zh-CN', 
                       help='目标语言代码：\n'
                            'zh-CN - 简体中文\n'
                            'zh-TW - 繁体中文\n'
                            'ja - 日语\n'
                            'en - 英语')
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"[错误] 文件不存在: {args.input}")
        exit(1)
    
    main(args.input, args.target)