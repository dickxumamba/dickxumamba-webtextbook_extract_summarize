# -*- coding: utf-8 -*-
"""
OpenGeology 爬虫脚本

本脚本用于从 opengeology.org/textbook 网站爬取指定章节的内容，并将内容保存为 Markdown 文件，格式符合GPT-4o分析使用要求。
指定爬取章节：第1章到第8章，保存章节正文内容，遇到"Chapter X Review Quiz"停止，不包含参考文献部分。
脚本将保留原有章节内标题和段落结构，过滤导航栏、页脚、侧边栏等无关元素，对正文中所有下划线文字进行特殊标注：转为**加粗+斜体**并加下划线标记。
同时下载正文图片并替换为本地链接（保存在各章节的images子文件夹下），视频内容仅插入原始URL链接。

依赖：
- Python 3.x
- requests
- beautifulsoup4
"""

import os
import time
import re
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# 章节信息列表：每项包含章节数字、URL后缀、章节名称
chapters = [
    {"num": 1, "slug": "1-understanding-science", "title": "Understanding Science"},
    {"num": 2, "slug": "2-plate-tectonics", "title": "Plate Tectonics"},
    {"num": 3, "slug": "3-minerals", "title": "Minerals"},
    {"num": 4, "slug": "4-igneous-processes-and-volcanoes", "title": "Igneous Processes and Volcanoes"},
    {"num": 5, "slug": "5-weathering-erosion-and-sedimentary-rocks", "title": "Weathering, Erosion, and Sedimentary Rocks"},
    {"num": 6, "slug": "6-metamorphic-rocks", "title": "Metamorphic Rocks"},
    {"num": 7, "slug": "7-geologic-time", "title": "Geologic Time"},
    {"num": 8, "slug": "8-earth-history", "title": "Earth History"},
]

base_url = "http://opengeology.org/textbook/"  # 基础URL
output_dir = "OpenGeology_Textbook"  # 输出主目录

# 创建输出主目录
os.makedirs(output_dir, exist_ok=True)

# 统一的请求头，模拟浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def process_text(elem):
    """
    递归处理bs4元素，将HTML结构转为Markdown文本，对 <u> 下划线标签进行特殊标注。
    支持标签：<u>, <strong>/<b>, <em>/<i>。
    其他标签(如<a>、<span>等)仅保留文本内容，不输出标签符号。
    """
    text = ""
    if isinstance(elem, NavigableString):
        # 直接返回文本内容
        return str(elem)
    if not isinstance(elem, Tag):
        return ""
    # 处理下划线文本：加粗+斜体并标记下划线（Markdown中用 _**text**_ 表示）
    if elem.name == 'u':
        inner_text = "".join(process_text(c) for c in elem.children)
        return f"_**{inner_text}**_"
    # 处理粗体
    if elem.name in ['strong', 'b']:
        inner_text = "".join(process_text(c) for c in elem.children)
        return f"**{inner_text}**"
    # 处理斜体
    if elem.name in ['em', 'i']:
        inner_text = "".join(process_text(c) for c in elem.children)
        return f"*{inner_text}*"
    # 处理上标（保留文本）
    if elem.name == 'sup':
        inner_text = "".join(process_text(c) for c in elem.children)
        return f"{inner_text}"
    # 处理链接标签（仅保留文本，不构造Markdown链接）
    if elem.name == 'a':
        inner_text = "".join(process_text(c) for c in elem.children)
        return inner_text
    # 对于其他标签，递归处理子元素
    return "".join(process_text(c) for c in elem.children)


# 遍历每个章节
for chap in chapters:
    num = chap["num"]
    slug = chap["slug"]
    title = chap["title"]
    
    # 创建章节目录和图片子目录
    chapter_dir = os.path.join(output_dir, f"Chapter_{num}_{title.replace(' ', '_')}")
    images_dir = os.path.join(chapter_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 构建章节URL
    url = f"{base_url}{slug}/"
    print(f"正在下载章节 {num}：{title} ...")
    print(f"URL: {url}")

    try:
        res = requests.get(url, headers=headers)
        res.encoding = res.apparent_encoding
        html = res.text
        print(f"获取页面成功，状态码：{res.status_code}")
    except Exception as e:
        print(f"无法获取章节 {num}: {e}")
        continue

    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找主要内容区域
    main_content = soup.find('div', {'class': 'entry-content'})
    if not main_content:
        print("未找到主要内容区域")
        continue
        
    # 查找"Review Quiz"部分的标题标签
    review_tag = main_content.find(lambda tag: tag.name and 'Review Quiz' in tag.get_text())
    if review_tag:
        print("找到 Review Quiz 部分")
        # 获取 Review Quiz 之前的所有兄弟元素（即正文内容）
        siblings = list(review_tag.find_previous_siblings())
        siblings.reverse()
        content_elems = siblings
    else:
        print("未找到 Review Quiz 部分，使用所有内容")
        content_elems = main_content.find_all(recursive=False)

    # 准备用于Markdown保存的行列表
    md_lines = []
    image_count = 0  # 本章节图像计数

    # 依次处理正文元素
    for elem in content_elems:
        if elem.name and elem.name.startswith('h'):
            # 处理标题标记
            level = elem.name[1:]
            try:
                level = int(level)
            except:
                level = 2
            prefix = "#" * level
            heading_text = process_text(elem).strip()
            if heading_text:
                md_lines.append(f"{prefix} {heading_text}")
                md_lines.append("")  # 标题后空行

        elif elem.name == 'p':
            # 段落：提取并处理其中可能的下划线等
            para = process_text(elem).strip()
            if para:
                md_lines.append(para)
                md_lines.append("")

        elif elem.name in ['ul', 'ol']:
            # 列表：遍历li项
            li_tags = elem.find_all('li', recursive=False)
            for idx, li in enumerate(li_tags, start=1):
                li_text = process_text(li).strip()
                if li_text:
                    if elem.name == 'ul':
                        md_lines.append(f"- {li_text}")
                    else:
                        md_lines.append(f"{idx}. {li_text}")
            md_lines.append("")

        elif elem.name == 'figure':
            # 处理图像及其说明
            img = elem.find('img')
            if img and img.get('src'):
                img_url = img['src']
                # 解析图像URL：相对路径则拼接为完整URL
                if img_url.startswith("//"):
                    img_url = "http:" + img_url
                elif img_url.startswith("/"):
                    img_url = "http://opengeology.org" + img_url
                alt = img.get('alt', '')
                caption_tag = elem.find('figcaption')
                caption = caption_tag.get_text().strip() if caption_tag else alt
                # 下载图片
                image_count += 1
                ext = os.path.splitext(img_url)[1]
                if not ext:
                    ext = ".png"
                img_filename = f"Image{image_count}{ext}"
                img_path = os.path.join(images_dir, img_filename)
                try:
                    img_res = requests.get(img_url, headers=headers)
                    with open(img_path, 'wb') as f_img:
                        f_img.write(img_res.content)
                    print(f"下载图片：{img_filename}")
                except Exception as e:
                    print(f"无法下载图片 {img_url}: {e}")
                # 插入Markdown图片链接
                md_lines.append(f"![{caption}](images/{img_filename})")
                md_lines.append("")

        elif elem.name == 'img':
            # 单独的<img>标签（若不在<figure>内）
            img_url = elem['src']
            if img_url.startswith("//"):
                img_url = "http:" + img_url
            elif img_url.startswith("/"):
                img_url = "http://opengeology.org" + img_url
            alt = elem.get('alt', '')
            image_count += 1
            ext = os.path.splitext(img_url)[1]
            if not ext:
                ext = ".png"
            img_filename = f"Image{image_count}{ext}"
            img_path = os.path.join(images_dir, img_filename)
            try:
                img_res = requests.get(img_url, headers=headers)
                with open(img_path, 'wb') as f_img:
                    f_img.write(img_res.content)
                print(f"下载图片：{img_filename}")
            except Exception as e:
                print(f"无法下载图片 {img_url}: {e}")
            md_lines.append(f"![{alt}](images/{img_filename})")
            md_lines.append("")

        elif elem.name == 'iframe':
            # 视频处理：插入Markdown链接
            video_url = elem.get('src')
            if video_url:
                md_lines.append(f"[Video]({video_url})")
                md_lines.append("")

        else:
            # 其他标签（例如div、table等）：尝试提取文本
            text = process_text(elem).strip()
            if text:
                md_lines.append(text)
                md_lines.append("")

    # 将Markdown内容写入文件
    filename = f"Chapter_{num}_{title.replace(' ', '_')}.md"
    filepath = os.path.join(chapter_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f_out:
        f_out.write("\n".join(md_lines))

    print(f"已保存 {filename}，共 {len(md_lines)} 行")
    # 暂停1秒，避免请求过快
    time.sleep(1)

print("所有章节处理完毕！") 