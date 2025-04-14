import os
import random
import time
from crawl4ai import WebCrawler
from crawl4ai.extractor import *
from crawl4ai.crawler import *


def clean_title(title):
    """清理标题文本"""
    if title and "项目的链接 - " in title:
        return title.replace("项目的链接 - ", "")
    return title


def scrape_behance_projects(max_projects=100, proxy=None, name="old"):
    # 配置爬虫参数
    crawler = WebCrawler(
        proxy=proxy,
        screenshot=False,
        window_size=(1920, 1080),
        scroll={
            "scroll_step": 400,
            "scroll_pause": 1.5,
            "max_scrolls": 50,
            "auto_scroll": True
        }
    )

    # 执行爬取
    url = f"https://www.behance.net/search/projects/{name}"
    result = crawler.run(
        url=url,
        extractor=CSSExtractor(
            css_selector="a.ProjectCoverNeue-coverLink-U39",
            schema={
                "url": ["attr", "href"],
                "title": ["attr", "title"]
            }
        )
    )

    # 处理结果
    projects = []
    seen_urls = set()
    for item in result.data:
        href = item['url']
        title = clean_title(item['title'])

        if href and href not in seen_urls:
            if href.startswith("/"):
                href = f"https://www.behance.net{href}"

            projects.append({
                "title": title,
                "url": href
            })
            seen_urls.add(href)

            if len(projects) >= max_projects:
                break

    print(f"Found {len(projects)} projects")
    return projects, [p['url'] for p in projects]


def scrape_behance_details(urls, proxy=None, name="output"):
    # 创建输出目录
    os.makedirs(name, exist_ok=True)

    # 配置图片爬虫
    img_crawler = WebCrawler(
        proxy=proxy,
        screenshot=False,
        window_size=(1920, 1080),
        scroll={
            "scroll_step": 400,
            "scroll_pause": 1,
            "max_scrolls": 3,
            "auto_scroll": True
        }
    )

    for i, url in enumerate(urls):
        print(f"Processing project {i + 1}/{len(urls)}: {url}")

        # 提取图片
        result = img_crawler.run(
            url=url,
            extractor=CSSExtractor(
                css_selector="img.ImageElement-image-SRv",
                schema={"src": ["attr", "src"]}
            )
        )

        # 下载图片
        for img in result.data:
            if img['src']:
                download_image(img['src'], name)

        time.sleep(random.uniform(1, 2))


def download_image(url, folder):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = url.split('/')[-1].split('?')[0]
            with open(f"{folder}/{filename}", 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")


def main():
    # 配置参数
    PROXY = "http://10.7.100.40:9910"  # 你的代理地址
    SEARCH_TERM = "landrover Defender"

    # 第一步：抓取项目列表
    projects, project_urls = scrape_behance_projects(
        max_projects=300,
        proxy=PROXY,
        name=SEARCH_TERM
    )

    # 第二步：抓取项目详情和图片
    scrape_behance_details(
        project_urls,
        proxy=PROXY,
        name=SEARCH_TERM.replace(" ", "")
    )

    print("任务完成!")


if __name__ == "__main__":
    main()