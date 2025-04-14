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


def get_cookies(cookies: str):
    # 提供的cookie字符串
    cookie_string = cookies

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


def scrape_behance_projects(max_projects=100, scroll_delay=1.5, proxy=None, name="old"):
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
            browser = p.chromium.launch(headless=True)
            context_options = {"viewport": {"width": 1920, "height": 1080}}
            if proxy:
                context_options["proxy"] = proxy
            # 设置cookies
            context = browser.new_context(**context_options)
            # context.add_cookies(get_cookies(
            #     'csrftoken=f0da77587c76532b19b4fee9ae4986b0; _routing_id="4fcc2161-5528-4527-b6dc-cfd83b4d1121"; sessionFunnelEventLogged=1; _auth=1; _pinterest_sess=TWc9PSYzcmJua0MrTWtka0ZXYm0xWDJ5VXdDZTgvN1JLV1NJREY4Q1dKNi94UFBIT3QrZkcxZTdWbVVJbkRVdlRHSnJzcWE3Ry9yYWVqQkt3QnRnaVZwQkNRS2hvc3I5cXpicUhiZGpycWVBRzREeEM4Vmdpc3JQbVltaFlLdGhCRUFjcXFhVDl1blZKS3ZRY3Znd2VJUGZmV25yMEhZUnpMd2dNcjVCWHpjdjV4dllZUnhPUExMUUE1djNJRGNnajhEQy9TbkQxVk41UVdIK0RvNUNQc3MxMTlySHB1WThZcHVlemNOekswei8xWFdSYTFCT2dIakNkOXhjSTNwOExXK1J1MU96VDhMaE1XMVdtNmg2NXd5ZWVOU0VXVHM2L2hTM2lJclFtcFBQdlJWQUNlNWpmNEZ2OUlKQlhOYkl4WmpkRmtmQmo5K1NFNFFLdmo5bnc1OCtWWnJZQXNCbTh0MXFRWTBOYlhXdjhqMzdISEtFMmNXOG1ZVVU5UzR0TlFocUpUUDk0NUZCelcvOTVvZzlOUEV6UXFnWEtOWFhZM0tLRjduL2ovWTJDZWFMQytML25pVWJkZ1BwK0RUMWh1Y3FrUHZPZ1YwUk95MHpPYWhkRTd6RVpZTGgraGhaQjh2N1h3Z1g0ZEJrei80ZWJ3UFNnQVpkM0lxVWNzeDc3bkZ2MDZEbEdnb2F4a0JkTEFhTzhhLy9Pb2RnU0JtbGc1TWUwb3Nmb2VZY0F6Tnkzc1RVQlFRd3lHcEhUZjZscnRlMnNKR0NoWHVXMVRHUXV3R2hMa2hSQ0Npb1FMZmpSdGc3blVMVTlKR2R0eVJmUEc0ZkdObTB5cS9FcDRrZkZXdUxpSHV5NWxUNll2QjFtREFsTU0wS2R6U09kN2d6aCthb0lZNDFKZzJKaTZ2QjlRR1RWbXk0SjFiWWdVeENWNVlSejNnT0dXbzdWb2FPT20wYnRVZXN2cUxHMFdua25IOFRrYTV4OWFUZjdmY0lCeUpRK0I2eGFJWlowdmZaWGU3UUhDRk95THl5RndrVDFUYWxmR25uWjJYclNuUHV2cU5OVFVaaHlBMTZ5VVI1M2Qva3U5MVBBL1JkOFIyNkhsTGFjOXY0emJQU1RiV1RBWlVsT2I3UVZBRDRzY3IrSVV2T3F6SmF4ZHdaMmFsS0JyUmRGSTA4enFJa1JkSmo1RkQ3Nm5CcWlUNzhQVFBOYUhwL3p1V2wrclFZd1JyVTJFT3M4Y2dkZmVkamJBRExBYVJsMFNuZW1qSWltSWZqZnpTcm5TRUxFWDdtQmZ1QitiNlZiS0NMM1FWR0J4TlQwZ2lxczFBRm91bG0rQjc3R0hjOSs3WXlsMElHTjcyMUtWbytxQUNUR3VPNDRNQkR0VXBxemZ2YjU2VVNTeHFLUjk4R2FWUU9kRUNiQUlHVytNVWpGSDMyZnpLb0IzTyt4VmJDamt4cWg4aEpMclNjUWNXZHdiRkFXTElIUFAxRU5jSU1IUWF1N1pRRTZFTWdTUGg0V0ZLTWxxVzViYS9BS0QzZDJxSlJyUjR6TFJrUy9jTW8yN3NRLytlUnlVSTVkc1NJUUY1cTREeEthaHZocDZzVEpuM1MxaG1kN0cvakU2YWF6UFltRXNXRnhJc09teXlseVdLSDZCajErd2N1cWlEcCs5MS80Mi9rdTgzNGtGZTRWcWVqQk5xUnNqYWhKZS9wdHBLMUFyUFh3Z3lJZjRnSDlSQ1RMTXVXWERmcUNEU2licGxzelBhaHJOTUc1YVlsaXgvc2lkSUR5dEZuYVQ3Y3EmdXFHS1c2cFBLcUlucjA0WkV1V3l2YUM0UTY4PQ==; __Secure-s_a=UEpPdElXZlErMUpMbUlFRHVncnM0NHhJc3NtRjcvL2RlVzRsM01YWE9Gam5sSzJ1cGE2SXJZd3JQQ3ZxeTJ1WjVCZlB1cXdHTEIrZ01FTy96RWtNdnAwRXZWNjlnYis3WHA5cnMzU3ZVWVFzMThPS3NITkV1M0hSbStzc3oxeVQ4Zng4NmgvNWhZbmkzNHc2YWJWSWlMbjNwZ2JCcUE2OTNNSi9hYWEwR1EyNnNTU1l5QU9kTnhqc1BPaVhoTEZnYm1WM2F5TXVXbERCY2R0TWwvOFlHd1ZqaWpZejUxRElvcDN5RzE2ejVUMVBUR2NvM0NQbEthS0hWNGlkSVpjZVpxZ1pwRDZBWjl1NHV2SW9xYjUzdnBJZHErQzdGV1htdEVHV04vd3pnQk9ON05xZkVPSXBoWEh1T2M4V0V3c05lZ1hVVUx3WHJxQ1dzalFGSlNRNU1HT012bk1QU1UyeC8rOFJTc3F0U1cyc3YyUW1mME1pN2IyTWNDcFNjbTFFMTdINGFIQlFnd1U0TDFhdDZzVG1tZmdCMmtPRVp2TGhkRHRYam5lUDhjbmM4OGw4UWlkTEZDUGIyZFdJQUltMjJ3amFlT1VSY2Q3Q05ET1VJVTRBazM3TGFxbXpUYXY4aGdYaVkvVVpWWS9vUWluNzZjQzBiMG1EdUJtd3lxcHRkV29iWmxWWDBFbHhKSjFpQmxBVGZPOGwydnRHbTVmMTUzWWdFaW1OVFl6c21sVmo5cXNYQ1VQWkxnbTZHdmhlcEFyTi9Kai9XbEFiRnh0SEZtNndxdTViYjFRam02YVRYRkViRUhoSVNESTVKb2FPR0xuUEVuVmR3bEIxcEU4anBHRlpLMGRUbzUxZHNhblRJOWdEV2VBVmxHbFkrV25hb2Zka21pWFE5Zk4yWlU5QzlRNWFUOWlQTlNnbDVNcHlRSHR4L3lXSFdKTU9lVDVoazBFaW05N2N4VG8zVmJuQVBOVmR5SE44Zyt5cUNVK1pVRmhVMVArRTdZU3d3UDV5eHQ5RlJFRGxTakdKM2U2MGp2WUZoM1JNa1dtdk96RkU4K3YwZkFVcDBiSzh2RlR4Mm5QQWc2TlI4YXdOaDl0RkJkU3ZWVUVEMTNkRnNDT2tibVJYRXNRTG9odmU0L0w5TzUzU0VqeFNWdFJUVHRpREJwVndtLzB6OG9JVUo1RXorNWVsWWlVUFd4K21nZmZOaDd5cUpxVjFkaDA4WldvbVhpQjkwcjlYK1FQNnVHR3p3Z3BIYVdqUW1EbXZLc3B2YTAwY0RUNzNZY1hWZ1dPc09lbHREdlF3OVltU1dOT1lzd1FnQ3lvbkVDZz0mU28yMWJJdGNVTmFSanNrUlhpSlRWZllGQTBjPQ==; _b="AYfYZ+l4jd5M65FWgISue0hOWIiuVXgmNcykg/Pjx7UAzqIIvQGJTmsTBBgAIp2doPU="; cm_sub=allowed')
            # )
            page = context.new_page()

            # 访问搜索页面
            url = f"https://www.pinterest.com/search/pins/?q={name}"
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
                links = page.locator("a.nrl").all()
                print(f"当前页面上找到 {len(links)} 个项目")

                #     # 处理新发现的链接
                #     new_found = False
                #
                for link in links:
                    # print(link.get_attribute("data-srcset")) #none
                    print(link.get_attribute("href"))
                    # srcset = link.get_attribute("srcset")
                    # high_res_link = srcset.split(", ")[-1].split(" ")[0]
                    # src = link.get_attribute("srcset")
                    # print(src)
            #         title = link.get_attribute("title")
            #
            #         # 处理相对URL
            #         if href and href.startswith("/"):
            #             href = f"https://www.behance.net{href}"
            #
            #         # 跳过已处理的URL
            #         if not href or href in seen_urls:
            #             continue
            #
            #         # 清理标题
            #         clean_text = clean_title(title)
            #
            #         # 保存项目信息
            #         projects.append({
            #             "title": clean_text,
            #             "url": href,
            #         })
            #         seen_urls.add(href)
            #         new_found = True
            #         count += 1
            #         print(f"[{count}/{max_projects}]  找到项目: {clean_text}")
            #
            #         # 如果达到目标数量，退出循环
            #         if count >= max_projects:
            #             break
            #
            #     # 如果达到目标数量，退出最外层循环
            #     if count >= max_projects:
            #         break
            #
            #     # 如果没有找到新链接但还未达到目标数量，尝试滚动加载更多
            #     if not new_found and count < max_projects:
            #         print(f"滚动加载更多内容... 当前: {count}/{max_projects}")
            #         # 滚动到页面底部
            #         page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            #         # 等待内容加载
            #         time.sleep(scroll_delay)
            #
            #         # 检查是否还有更多内容可加载
            #         retry_count = 0
            #         scroll_again = True
            #
            #         while retry_count < 5 and not new_found and scroll_again:
            #             page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            #             time.sleep(scroll_delay)
            #
            #             # 检查是否加载了新内容
            #             current_links_count = len(seen_urls)
            #             new_links = page.locator("a.ProjectCoverNeue-coverLink-U39").all()
            #
            #             for link in new_links:
            #                 href = link.get_attribute("href")
            #                 if href and href.startswith("/"):
            #                     href = f"https://www.behance.net{href}"
            #                 if href and href not in seen_urls:
            #                     scroll_again = True
            #                     break
            #             else:
            #                 scroll_again = False
            #
            #             retry_count += 1
            #
            #         # 如果3次重试后仍无新内容，认为已达到末尾
            #         if not scroll_again:
            #             print("已到达内容底部，无法加载更多项目")
            #             break
            #
            # print(f"爬取完成! 共获取 {len(projects)} 个作品集")
            # # 关闭浏览器
            # browser.close()
            # # 打印结果
            # print(json.dumps(projects[:5], ensure_ascii=False))  # 只打印前5个项目作为示例
            # project_urls = [project['url'] for project in projects]
            #
            # return projects, project_urls
        finally:
            # 确保无论如何都关闭浏览器，释放资源
            if browser:
                browser.close()


def scrape_behance_details(urls: list[str | Any], proxy=None, name: str = None):
    """
    爬取Behance项目的详情页

    url:详情地址
    Returns:
        项目列表，包含标题、链接和ID
    """
    num = 0
    # cookie = ""
    with sync_playwright() as p:
        # 启动浏览器（可选择headless=False查看浏览过程）
        browser = p.chromium.launch(headless=True)
        context_options = {"viewport": {"width": 1920, "height": 1080}}
        if proxy:
            context_options["proxy"] = proxy
        # 设置cookies
        # context.add_cookies(cookies)
        context = browser.new_context(**context_options)
        page = context.new_page()

        for url in urls:

            try:
                num += 1
                # 访问详情页
                page.goto(url)
                print(f"正在访问第{num}个作品集，详情页: {url}")

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
                    down_imgs(image_urls, proxy, name)

                # 添加延迟以防止被封IP
                time.sleep(2)

            except Exception as e:
                print(f"处理页面 {url} 时出错: {e}")
        browser.close()


def get_response(url, headers, proxy=None, name=None):
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


def down_imgs(imgs, proxy=None, name=None):
    threadings = []
    for img in imgs:
        t = threading.Thread(target=tps, args=(img, proxy, name))
        threadings.append(t)
        t.start()

    for x in threadings:
        x.join()

    print(f"多线程下载图片完成!")


def tps(img_url, proxy=None, name=None):
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
    r = get_response(img_url, headers, proxy)
    time.sleep(1)
    name_os = name.replace(" ", "")
    os.makedirs(name_os, exist_ok=True)
    with open(f'{name_os}/{img_name}', 'wb') as f:
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
    projects, project_urls = scrape_behance_projects(max_projects=300, proxy=proxy, name="Cadillac")

    # 第二步：抓取项目详情和图片
    scrape_behance_details(project_urls, proxy=proxy, name="landrover Defender")

    print("任务完成!")


main()
