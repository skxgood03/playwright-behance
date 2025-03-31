import json
import os
import random
import threading
import time
from typing import Any

import requests
from playwright.sync_api import sync_playwright


def clean_title(title):
    """清理标题文本"""
    # 移除"项目的链接 - "前缀
    if title and "项目的链接 - " in title:
        return title.replace("项目的链接 - ", "")
    return title


def get_cookies(url):
    # 提供的cookie字符串
    cookie_string = ""

    # 解析cookie字符串为字典列表
    cookies = []
    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.behance.net',  # 指定cookie的域
                'path': '/'
            })
    return cookies


def scrape_behance_projects(max_projects=10, scroll_delay=1.5, proxy=None):
    """
    爬取Behance项目

    Args:
        max_projects: 最大爬取项目数
        scroll_delay: 每次滚动后等待加载的时间(秒)

    Returns:
        项目列表，包含标题，详情url
    """

    with sync_playwright() as p:
        browser = None
        try:
            # 启动浏览器
            browser = p.chromium.launch(headless=False)
            context_options = {"viewport": {"width": 1920, "height": 1080}}
            if proxy:
                context_options["proxy"] = proxy
            # 设置cookies
            # context.add_cookies(cookies)
            context = browser.new_context(**context_options)
            page = context.new_page()

            # 访问搜索页面
            url = f"https://www.behance.net/search/projects/jetour?tracking_source=typeahead_nav_recent_suggestion"
            page.goto(url)
            print(f"访问页面: {url}")

            # 等待页面加载
            page.wait_for_load_state("networkidle")

            # 追踪已爬取的项目URL避免重复
            projects = []
            seen_urls = set()

            # 设置项目计数器显示爬取进度
            count = 0
            print(f"开始爬取，目标数量: {max_projects} 个项目")

            while count < max_projects:
                # 获取当前页面上的所有项目链接
                links = page.locator("a.ProjectCoverNeue-coverLink-U39").all()
                print(f"当前页面上找到 {len(links)} 个项目")

                # 处理新发现的链接
                new_found = False

                for link in links:
                    href = link.get_attribute("href")
                    title = link.get_attribute("title")

                    # 处理相对URL
                    if href and href.startswith("/"):
                        href = f"https://www.behance.net{href}"

                    # 跳过已处理的URL
                    if not href or href in seen_urls:
                        continue

                    # 清理标题
                    clean_text = clean_title(title)

                    # 保存项目信息
                    projects.append({
                        "title": clean_text,
                        "url": href,
                    })
                    seen_urls.add(href)
                    new_found = True
                    count += 1
                    print(f"[{count}/{max_projects}]  找到项目: {clean_text}")

                    # 如果达到目标数量，退出循环
                    if count >= max_projects:
                        break

                # 如果达到目标数量，退出最外层循环
                if count >= max_projects:
                    break

                # 如果没有找到新链接但还未达到目标数量，尝试滚动加载更多
                if not new_found and count < max_projects:
                    print(f"滚动加载更多内容... 当前: {count}/{max_projects}")
                    # 滚动到页面底部
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    # 等待内容加载
                    time.sleep(scroll_delay)

                    # 检查是否还有更多内容可加载
                    retry_count = 0
                    scroll_again = True

                    while retry_count < 5 and not new_found and scroll_again:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(scroll_delay)

                        # 检查是否加载了新内容
                        current_links_count = len(seen_urls)
                        new_links = page.locator("a.ProjectCoverNeue-coverLink-U39").all()

                        for link in new_links:
                            href = link.get_attribute("href")
                            if href and href.startswith("/"):
                                href = f"https://www.behance.net{href}"
                            if href and href not in seen_urls:
                                scroll_again = True
                                break
                        else:
                            scroll_again = False

                        retry_count += 1

                    # 如果3次重试后仍无新内容，认为已达到末尾
                    if not scroll_again:
                        print("已到达内容底部，无法加载更多项目")
                        break

            print(f"爬取完成! 共获取 {len(projects)} 个作品集")
            # 关闭浏览器
            browser.close()
            # 打印结果
            print(json.dumps(projects[:5], ensure_ascii=False))  # 只打印前5个项目作为示例
            project_urls = [project['url'] for project in projects]

            return projects, project_urls
        finally:
            # 确保无论如何都关闭浏览器，释放资源
            if browser:
                browser.close()


def scrape_behance_details(urls: list[str | Any], proxy=None):
    """
    爬取Behance项目的详情页

    url:详情地址
    Returns:
        项目列表，包含标题、链接和ID
    """
    # cookie = ""
    with sync_playwright() as p:
        # 启动浏览器（可选择headless=False查看浏览过程）
        browser = p.chromium.launch(headless=False)
        context_options = {"viewport": {"width": 1920, "height": 1080}}
        if proxy:
            context_options["proxy"] = proxy
        # 设置cookies
        # context.add_cookies(cookies)
        context = browser.new_context(**context_options)
        page = context.new_page()

        for url in urls:
            try:
                # 访问详情页
                page.goto(url)
                print(f"访问详情页: {url}")

                # 等待页面加载
                page.wait_for_load_state("networkidle")

                # 提取图片链接
                links = page.locator("img.ImageElement-image-SRv").all()
                print(f"当前页面上找到 {len(links)} 个图片")

                image_urls = []
                for link in links:
                    src = link.get_attribute("src")
                    if src:
                        image_urls.append(src)

                if image_urls:
                    down_imgs(image_urls, proxy)

                # 添加延迟以防止被封IP
                time.sleep(2)

            except Exception as e:
                print(f"处理页面 {url} 时出错: {e}")
        browser.close()


def get_response(url, headers, proxy=None):
    i = 0
    while i < 4:
        try:
            # 如果有代理则使用代理
            proxies = {"http": proxy['server'], "https": proxy['server']} if proxy else None
            response = requests.get(url, headers=headers, timeout=10, proxies=proxies)
            return response
        except requests.exceptions.RequestException:
            i += 1
            print(f">> 获取网页出错，6S后将重试获取第：{i} 次")
            time.sleep(i * 2)


def down_imgs(imgs, proxy=None):
    threadings = []
    for img in imgs:
        t = threading.Thread(target=tps, args=(img, proxy))
        threadings.append(t)
        t.start()

    for x in threadings:
        x.join()

    print(f"恭喜，多线程下载图片完成!")


def tps(img_url, proxy=None):
    ua_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36Chrome 17.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0Firefox 4.0.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
    ]
    headers = {
        'Connection': 'close',
        "User-Agent": random.choice(ua_list)
    }
    img_name =  img_url.split('/')[-1]
    r = get_response(img_url, headers, proxy)
    time.sleep(1)
    with open(f'old/{img_name}', 'wb') as f:
        f.write(r.content)
    print(f">> {img_name}下载图片成功")


def main():
    # 确保下载目录存在
    os.makedirs('old', exist_ok=True)
    proxy = {
        "server": "http://10.7.100.40:9910"
    }
    requests_proxy = proxy['server']
    # 第一步：抓取项目列表
    projects, project_urls = scrape_behance_projects(max_projects=10, proxy=proxy)

    # 第二步：抓取项目详情和图片
    scrape_behance_details(project_urls, proxy=proxy)

    print("任务完成!")


main()
