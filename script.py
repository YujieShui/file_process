# -*- coding: utf-8 -*-
"""
文件列表输出工具

这个脚本用于遍历指定目录及其子目录，并输出所有文件夹和文件的名称。
它会忽略隐藏文件（以 '.' 开头的文件）。

使用方法：
    python script.py <文件夹路径>

参数说明：
    <文件夹路径>    要遍历的目录路径

示例：
    python script.py ./test

注意事项：
    1. 确保指定的目录路径存在。
    2. 脚本将输出每个文件夹的名称及其包含的文件名称，文件名称之间用空行分隔。
"""

import os
import sys

def list_files(directory):
    for root, dirs, files in os.walk(directory):
        # 获取当前目录的相对路径
        relative_path = os.path.relpath(root, directory)
        if relative_path == '.':
            folder_name = os.path.basename(root)
        else:
            folder_name = relative_path
        
        # 输出文件夹名称
        print(folder_name)
        
        # 输出文件名称，忽略隐藏文件
        for file in files:
            if not file.startswith('.'):  # 忽略隐藏文件
                print(file)
        print()  # 输出空行分隔不同文件夹

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python script.py <文件夹路径>")
        sys.exit(1)

    directory_path = sys.argv[1]  # 从命令行参数获取文件夹路径
    list_files(directory_path)