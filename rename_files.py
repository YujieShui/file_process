# -*- coding: utf-8 -*-
"""
批量文件重命名工具

这个脚本用于批量重命名文件，可以递归处理指定目录下的所有文件。
支持预览模式，可以在实际重命名之前查看将要进行的更改。

功能特点：
    - 递归处理子目录
    - 支持预览模式
    - 支持将指定字符串替换为新字符串
    - 支持完全删除指定字符串

使用方法：
    1. 基本用法（删除模式）：
       python rename_files.py <目录路径> <要删除的字符串>
       例如：python rename_files.py ./test 111

    2. 替换模式：
       python rename_files.py <目录路径> <要替换的字符串> --new <新字符串>
       例如：python rename_files.py ./test 111 --new 222

参数说明：
    directory    要处理的目录路径
    pattern      要替换的字符串
    --new        替换后的新字符串（可选，默认为空，即删除模式）

使用示例：
    # 删除文件名中的 "111"
    python rename_files.py /path/to/directory 111

    # 将文件名中的 "111" 替换为 "222"
    python rename_files.py /path/to/directory 111 --new 222

注意事项：
    1. 建议首次使用时先在测试目录中尝试
    2. 重要文件请先备份
    3. 注意检查预览模式中显示的变更是否符合预期
"""

import os
import re
from pathlib import Path
import argparse

def rename_files(root_dir, mode='prefix', old_pattern='', new_pattern='', preview=True):
    # 使用 Path 对象处理路径
    root_path = Path(root_dir)
    
    # 检查目录是否存在
    if not root_path.exists():
        raise ValueError(f"目录 '{root_dir}' 不存在")
    
    # 记录找到的文件数量
    found_files = 0
    
    # 正则表达式模式：匹配 [数字] 格式
    prefix_pattern = r'^\[\d+\]\s*'
    
    # 递归遍历所有文件
    for file_path in root_path.rglob('*'):
        if file_path.is_file():  # 只处理文件，不处理文件夹
            old_name = file_path.name
            new_name = old_name
            
            if mode == 'prefix':
                # 删除前缀模式
                new_name = re.sub(prefix_pattern, '', old_name)
            else:
                # 字符串替换模式
                if old_pattern in old_name:
                    new_name = old_name.replace(old_pattern, new_pattern)
            
            # 如果文件名发生了变化
            if new_name != old_name:
                found_files += 1
                new_path = file_path.parent / new_name
                
                if preview:
                    print('预览更改: {} -> {}'.format(file_path, new_path))
                else:
                    try:
                        file_path.rename(new_path)
                        print('已重命名: {} -> {}'.format(file_path, new_path))
                    except Exception as e:
                        print('重命名失败 {}: {}'.format(file_path, str(e)))
    
    if found_files == 0:
        print("\n未找到需要重命名的文件")
    
    return found_files

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='批量重命名文件工具')
    parser.add_argument('directory', help='要处理的目录路径')
    parser.add_argument('--mode', choices=['prefix', 'replace'], default='replace',
                      help='重命名模式：prefix(删除[数字]前缀) 或 replace(替换字符串)')
    parser.add_argument('--pattern', help='要替换的字符串（仅在 replace 模式下使用）')
    parser.add_argument('--new', default='', help='替换后的新字符串（仅在 replace 模式下使用）')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 先预览
    print("\n=== 预览模式 ===")
    rename_files(args.directory, mode=args.mode, 
                old_pattern=args.pattern if args.pattern else '',
                new_pattern=args.new,
                preview=True)
    
    # 询问是否执行实际重命名
    response = input("\n是否执行实际重命名操作？(y/n): ")
    if response.lower() == 'y':
        print("\n=== 执行重命名 ===")
        rename_files(args.directory, mode=args.mode,
                    old_pattern=args.pattern if args.pattern else '',
                    new_pattern=args.new,
                    preview=False)
    else:
        print("\n操作已取消")

if __name__ == '__main__':
    main() 