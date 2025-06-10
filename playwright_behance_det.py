import random
import threading
import time

import requests
from playwright.sync_api import sync_playwright


def scrape_behance_details(url:str):
    """
    爬取Behance项目的详情页

    url:详情地址
    Returns:
        项目列表，包含标题、链接和ID
    """
    # cookie = ""
    with sync_playwright() as p:
        # 启动浏览器（可选择headless=False查看浏览过程）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # 访问搜索页面
        url = f"https://www.behance.net/gallery/215720541/JETOUR-T2-MV?tracking_source=search_projects|jetour&l=0"
        page.goto(url)
        print(f"访问页面: {url}")

        # 等待页面加载
        page.wait_for_load_state("networkidle")

        links = page.locator("img.ImageElement-image-SRv").all()
        print(f"当前页面上找到 {len(links)} 个项目")
        image_urls = []
        for link in links:
            src = link.get_attribute("src")
            image_urls.append(src)
        down_imgs(image_urls)
        browser.close()


def get_response(url, headers):
    i = 0
    while i < 4:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response
        except requests.exceptions.RequestException:
            i += 1
            print(f">> 获取网页出错，6S后将重试获取第：{i} 次")
            time.sleep(i * 2)


def down_imgs(imgs):
    threadings = []
    for img in imgs:
        t = threading.Thread(target=tps, args=(img,))
        threadings.append(t)
        t.start()

    for x in threadings:
        x.join()

    print(f"恭喜，多线程下载图片完成!")


def tps(img_url):
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
    img_name = img_url.split('/')[-1]
    r = get_response(img_url, headers)
    time.sleep(1)
    with open(f'new/{img_name}', 'wb') as f:
        f.write(r.content)
    print(f">> {img_name}下载图片成功")

scrape_behance_details("url")