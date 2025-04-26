# OpenGeology 教材爬虫

这是一个用于从 OpenGeology 网站（opengeology.org/textbook）爬取地质学教材内容的 Python 爬虫脚本。

## 功能特点

- 自动爬取教材第1-8章的内容
- 将内容转换为 Markdown 格式
- 自动下载并保存图片到本地
- 特殊处理下划线文本（转为加粗斜体并标记下划线）
- 保留原有章节的标题和段落结构
- 过滤无关元素（导航栏、页脚、侧边栏等）
- 遇到"Chapter X Review Quiz"时停止爬取，不包含参考文献部分

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保已安装 Python 3.x
2. 安装依赖包：`pip install -r requirements.txt`
3. 运行脚本：`python opengeology_crawler.py`

## 输出文件

- 爬取的内容将保存在 `OpenGeology_Textbook` 目录下
- 每个章节保存为一个独立的 Markdown 文件
- 图片文件保存在 `OpenGeology_Textbook/images` 目录下

## 注意事项

- 请确保网络连接正常
- 脚本会自动在请求之间添加1秒延迟，以避免对服务器造成过大压力
- 如果遇到下载失败的情况，脚本会继续处理下一个章节
