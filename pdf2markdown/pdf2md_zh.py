#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdfplumber
import os
import re
from pdfminer.high_level import extract_text
from tqdm import tqdm
import openai  # 添加OpenAI导入
from tenacity import retry, stop_after_attempt, wait_random_exponential
import requests
import json
import ollama  # 添加 ollama 导入

# 设置OpenAI API密钥
openai.api_key = 'your-api-key'  # 建议从环境变量获取

def extract_text_dual(pdf_path):
    """双引擎文本提取（优先pdfplumber，备选pdfminer）"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return '\n\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
    except:
        return extract_text(pdf_path)

def optimize_chinese_text(text):
    """针对中文的格式优化"""
    # 预处理 - 统一换行符
    text = text.replace('\r\n', '\n')
    
    # 移除页码（更严格的页码模式匹配）
    text = re.sub(r'\s*\d+\s*/\s*\d+\s*(?:页?)\s*', '', text)  # 移除 "x/y" 格式页码
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # 移除单独成行的数字
    text = re.sub(r'第\s*\d+\s*页\s*', '', text)  # 移除 "第x页" 格式
    
    # 处理因页面分隔导致的不当换行
    lines = text.split('\n')
    merged_lines = []
    skip_next = False
    
    for i in range(len(lines)):
        if skip_next:
            skip_next = False
            continue
            
        current_line = lines[i].strip()
        if not current_line:
            merged_lines.append('')
            continue
            
        # 检查当前行是否应该与下一行合并
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if (
                # 当前行结尾没有标点符号
                not any(current_line.endswith(p) for p in '。！？；.!?;，,）】」》』') and
                # 下一行不是新段落的开始标志
                not any(next_line.startswith(m) for m in ['第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']) and
                # 下一行不是空行
                next_line and
                # 当前行不是标题
                not current_line.startswith('#')
            ):
                merged_lines.append(current_line + next_line)
                skip_next = True
            else:
                merged_lines.append(current_line)
        else:
            merged_lines.append(current_line)
    
    text = '\n'.join(merged_lines)
    
    # 识别并保留段落（优化段落分隔）
    paragraphs = []
    current_para = []
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:  # 空行表示段落分隔
            if current_para:
                paragraphs.append(''.join(current_para))
                current_para = []
        else:
            # 检查是否是新段落的开始
            if (len(current_para) > 0 and 
                (line.startswith('    ') or  # 缩进
                 line[0].isupper() or  # 大写字母开头
                 any(line.startswith(marker) for marker in ['第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']) or  # 中文段落标记
                 line.endswith('：') or  # 以冒号结尾的标题
                 line.startswith('#'))  # Markdown标题
               ):
                paragraphs.append(''.join(current_para))
                current_para = []
            current_para.append(line)
    
    if current_para:
        paragraphs.append(''.join(current_para))
    
    # 合并段落成文本，使用两个换行符分隔
    text = '\n\n'.join(p for p in paragraphs if p.strip())
    
    # 清理格式
    text = re.sub(r'\s*([，。！？；：、）】」》』])\s*', r'\1', text)
    text = re.sub(r'\s*([（【「《『])\s*', r'\1', text)
    text = re.sub(r'([A-Za-z0-9])([\u4e00-\u9fff])', r'\1 \2', text)
    text = re.sub(r'([\u4e00-\u9fff])([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
    
    # 清理多余空行和广告文本
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'公众号懒人搜索，懒人专属群分享', '', text)
    text = re.sub(r'懒人专属群独享懒人微信：\s*lazyhelper', '', text)
    
    return text.strip()

def optimize_document_structure_ollama(text, model="qwen2.5"):
    """使用本地Ollama模型优化文档结构"""
    try:
        prompt = """
        
        以下是一份 Markdown 格式的文档。
        
        请你根据文档的内容和段落，进行如下处理：
        
        1. **仅调整文档的排版** —— 重新组织段落、调整空行、分割内容，但**不要对文档中的任何文字内容进行修改**;
        2. 排版美观，适合人阅读，去除多余的换行和空格
        3. 输出 markdown 格式的内容，不要给文章内容加上 ```markdown``` 标签。

        请严格按照以上要求，只进行格式排版调整，不改变任何原文内容。
        不要对文章内容进行总结和归纳。
 
        以下是需要优化的文档内容：
        
        """ + text
        
        try:
            # 使用 ollama 库直接调用模型
            response = ollama.generate(
                model=model,
                prompt=prompt,
                stream=False
            )
            return response['response'].strip()
        except ollama.ResponseError as e:
            if "model not found" in str(e):
                print(f"模型 {model} 未安装，请先运行 'ollama pull {model}'")
            else:
                print(f"Ollama调用错误: {str(e)}")
            return text
            
    except Exception as e:
        print(f"本地模型调用失败: {str(e)}")
        return text

def convert_pdf_to_md(pdf_path, md_path, use_local_model=True):
    """转换PDF到Markdown，支持本地模型选项"""
    try:
        # 提取文本
        text = extract_text_dual(pdf_path)
        
        # 基础格式优化
        optimized = optimize_chinese_text(text)
        
        # 添加Markdown格式
        title = os.path.splitext(os.path.basename(pdf_path))[0]
        content = f"# {title}\n\n{optimized}"
        
        # 使用本地或云端模型优化文档结构
        content = optimize_document_structure_ollama(content)
        
        # 添加目录(如果内容较长)
        if len(content.split('\n')) > 20:
            content = generate_toc(content)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"转换失败 {pdf_path}: {str(e)}")
        return False

def generate_toc(content):
    """生成目录"""
    lines = content.split('\n')
    toc = ['## 目录\n']
    headers = []
    
    for line in lines:
        if line.startswith('#'):
            level = line.count('#')
            if level > 1:  # 不包含文档标题
                title = line.strip('#').strip()
                toc.append('  ' * (level-2) + f'- [{title}](#{title})')
                headers.append(line)
    
    if len(headers) > 1:  # 只有多于一个标题时才添加目录
        return '\n'.join(lines[:2] + ['\n'] + toc + ['\n'] + lines[2:])
    return content

def batch_convert(input_dir="pdfs", output_dir="markdown", use_local_model=True):
    """批量转换，支持选择模型类型"""
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"在 {input_dir} 目录中未找到PDF文件")
        return

    success = 0
    for filename in tqdm(pdf_files, desc="转换进度"):
        pdf_path = os.path.join(input_dir, filename)
        md_filename = os.path.splitext(filename)[0] + ".md"
        md_path = os.path.join(output_dir, md_filename)
        if convert_pdf_to_md(pdf_path, md_path, use_local_model):
            success += 1
    
    print(f"转换完成: 成功 {success}/{len(pdf_files)} 个文件")

if __name__ == "__main__":
    batch_convert(use_local_model=True) 