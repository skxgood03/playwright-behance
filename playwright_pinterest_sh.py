import json
import os
import random
import threading
import time
from typing import Any

import requests
from playwright.sync_api import sync_playwright

from db.db_config import conn
from playwright_behance_sql import inster_data, upadate_portfolio

cursor = conn.cursor()


def clean_title(title):
    """清理标题文本"""
    # 移除"项目的链接 - "前缀
    if title and "项目的链接 - " in title:
        return title.replace("项目的链接 - ", "")
    return title


def get_cookies(cookies: str):
    cookie_list = []
    for cookie_pair in cookies.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)

            # 基础cookie字典
            cookie_dict = {
                'name': name,
                'value': value,
                'domain': '.pinterest.com',
                'path': '/',
                'secure': True,  # 添加secure标志
                'httpOnly': False,  # 添加httpOnly标志
                'sameSite': 'Lax',  # 添加sameSite属性
                'expires': -1  # 添加过期时间
            }

            # 对于特定的cookie添加特殊处理
            if name.startswith('__Secure-'):
                cookie_dict['secure'] = True

            cookie_list.append(cookie_dict)
    return cookie_list


# def scrape_behance_projects(max_projects=100, scroll_delay=1.5, proxy=None, name="old", max_retries=3):
#     def retry_with_timeout(func, timeout=30000, retries=2):
#         for attempt in range(retries):
#             try:
#                 return func()
#             except TimeoutError as e:
#                 if attempt == retries - 1:  # 最后一次尝试
#                     raise e
#                 print(f"超时，第{attempt + 1}次重试...")
#                 time.sleep(2)  # 重试前等待
#             except Exception as e:
#                 if attempt == retries - 1:
#                     raise e
#                 print(f"发生错误: {e}, 第{attempt + 1}次重试...")
#                 time.sleep(2)
#
#     with sync_playwright() as p:
#         browser = None
#         try:
#             browser = p.chromium.launch(headless=False)
#             context_options = {"viewport": {"width": 1920, "height": 1080}}  # 增加视口大小
#             if proxy:
#                 context_options["proxy"] = proxy
#
#             context = browser.new_context(**context_options)
#             page = context.new_page()
#
#             # 设置更长的超时时间
#             page.set_default_timeout(60000)  # 60秒超时
#
#             url = f"https://www.pinterest.com/search/pins/?q={name}"
#             page.goto(url)
#             print(f"访问页面: {url}")
#
#             # 等待页面加载，带重试机制
#             def wait_for_load():
#                 page.wait_for_load_state("networkidle")
#
#             retry_with_timeout(wait_for_load)
#
#             projects = []
#             seen_urls = set()
#             count = 0
#
#             while count < max_projects:
#                 time.sleep(scroll_delay)
#
#                 # 获取图片元素，带重试机制
#                 def get_links():
#                     # 等待至少一个图片元素可见
#                     page.wait_for_selector("div.XiG.zI7.iyn.Hsu img", state="visible", timeout=30000)
#
#                     # 使用更完整的选择器
#                     images = page.query_selector_all("div.XiG.zI7.iyn.Hsu img")
#                     return images
#
#                 links = retry_with_timeout(get_links)
#
#                 print(f"当前页面上找到 {len(links)} 个项目")
#                 new_found = False
#
#                 for link in links:
#                     try:
#                         # 获取srcset属性，带重试机制
#                         def get_srcset():
#                             return link.get_attribute("srcset")
#
#                         srcset = retry_with_timeout(get_srcset)
#
#                         if not srcset:
#                             continue
#
#                         high_res_url = None
#                         srcset_parts = srcset.split(", ")
#                         for part in srcset_parts:
#                             if "originals" in part:
#                                 high_res_url = part.split(" ")[0]
#                                 break
#
#                         if not high_res_url or high_res_url in seen_urls:
#                             continue
#
#                         count += 1
#                         print(f"提取到原始尺寸(4x)图片: {high_res_url}")
#                         projects.append({
#                             "title": name,
#                             "detail_url": high_res_url,
#                             "author": "未知",
#                             "author_url": "",
#                             "likes": 0,
#                             "views": 0,
#                             "search": name,
#                             "platform": "pinterest"
#                         })
#                         seen_urls.add(high_res_url)
#                         new_found = True
#
#                         print(f"[{count}/{max_projects}] 找到项目: {high_res_url}")
#
#                         if count >= max_projects:
#                             break
#                     except Exception as e:
#                         print(f"处理单个项目时出错: {e}")
#                         continue
#
#                 if count >= max_projects:
#                     break
#
#                 if not new_found and count < max_projects:
#                     print(f"滚动加载更多内容... 当前: {count}/{max_projects}")
#
#                     # 滚动操作带重试机制
#                     def scroll_page():
#                         page.evaluate("""
#                             window.scrollTo(0, document.body.scrollHeight);
#                             window.dispatchEvent(new Event('scroll'));
#                         """)
#
#                     retry_with_timeout(scroll_page)
#
#                     time.sleep(scroll_delay)
#
#                     retry_count = 0
#                     max_scroll_retries = 5
#                     scroll_again = True
#
#                     while retry_count < max_scroll_retries and not new_found and scroll_again:
#                         try:
#                             before_scroll = page.evaluate("() => window.pageYOffset")
#                             retry_with_timeout(scroll_page)
#                             time.sleep(scroll_delay)
#                             after_scroll = page.evaluate("() => window.pageYOffset")
#                             print(f"滚动前位置: {before_scroll}, 滚动后位置: {after_scroll}")
#                             if before_scroll == after_scroll:
#                                 retry_count += 1
#                                 continue
#
#                             links = retry_with_timeout(get_links)
#                             for link in links:
#                                 try:
#                                     srcset = retry_with_timeout(lambda: link.get_attribute("srcset"))
#                                     if not srcset:
#                                         continue
#
#                                     for part in srcset.split(", "):
#                                         if "originals" in part:
#                                             high_res_url = part.split(" ")[0]
#                                             if high_res_url not in seen_urls:
#                                                 scroll_again = True
#                                                 break
#                                     else:
#                                         scroll_again = False
#                                 except Exception as e:
#                                     print(f"处理滚动后的项目时出错: {e}")
#                                     continue
#
#                         except Exception as e:
#                             print(f"滚动加载时出错: {e}")
#                             retry_count += 1
#                             time.sleep(2)
#                             continue
#
#                         retry_count += 1
#
#                     if not scroll_again:
#                         print("已到达内容底部，无法加载更多项目")
#                         break
#
#             print(f"爬取完成! 共获取 {len(projects)} 个作品集")
#             project_urls = [project['detail_url'] for project in projects]
#             return projects, project_urls
#
#         except Exception as e:
#             print(f"发生严重错误: {e}")
#             return [], []
#
#         finally:
#             if browser:
#                 browser.close()

def scrape_behance_projects(max_projects=100, scroll_delay=1.5, proxy=None, name="old"):
    with sync_playwright() as p:
        browser = None
        try:
            # 启动浏览器
            browser = p.chromium.launch(headless=False)
            context_options = {"viewport": {"width": 1920, "height": 1080}}
            if proxy:
                context_options["proxy"] = proxy
            # 设置cookies
            context = browser.new_context(**context_options)
            context.add_cookies(get_cookies(
                'csrftoken=f0da77587c76532b19b4fee9ae4986b0; _auth=1; _pinterest_sess=TWc9PSYzcmJua0MrTWtka0ZXYm0xWDJ5VXdDZTgvN1JLV1NJREY4Q1dKNi94UFBIT3QrZkcxZTdWbVVJbkRVdlRHSnJzcWE3Ry9yYWVqQkt3QnRnaVZwQkNRS2hvc3I5cXpicUhiZGpycWVBRzREeEM4Vmdpc3JQbVltaFlLdGhCRUFjcXFhVDl1blZKS3ZRY3Znd2VJUGZmV25yMEhZUnpMd2dNcjVCWHpjdjV4dllZUnhPUExMUUE1djNJRGNnajhEQy9TbkQxVk41UVdIK0RvNUNQc3MxMTlySHB1WThZcHVlemNOekswei8xWFdSYTFCT2dIakNkOXhjSTNwOExXK1J1MU96VDhMaE1XMVdtNmg2NXd5ZWVOU0VXVHM2L2hTM2lJclFtcFBQdlJWQUNlNWpmNEZ2OUlKQlhOYkl4WmpkRmtmQmo5K1NFNFFLdmo5bnc1OCtWWnJZQXNCbTh0MXFRWTBOYlhXdjhqMzdISEtFMmNXOG1ZVVU5UzR0TlFocUpUUDk0NUZCelcvOTVvZzlOUEV6UXFnWEtOWFhZM0tLRjduL2ovWTJDZWFMQytML25pVWJkZ1BwK0RUMWh1Y3FrUHZPZ1YwUk95MHpPYWhkRTd6RVpZTGgraGhaQjh2N1h3Z1g0ZEJrei80ZWJ3UFNnQVpkM0lxVWNzeDc3bkZ2MDZEbEdnb2F4a0JkTEFhTzhhLy9Pb2RnU0JtbGc1TWUwb3Nmb2VZY0F6Tnkzc1RVQlFRd3lHcEhUZjZscnRlMnNKR0NoWHVXMVRHUXV3R2hMa2hSQ0Npb1FMZmpSdGc3blVMVTlKR2R0eVJmUEc0ZkdObTB5cS9FcDRrZkZXdUxpSHV5NWxUNll2QjFtREFsTU0wS2R6U09kN2d6aCthb0lZNDFKZzJKaTZ2QjlRR1RWbXk0SjFiWWdVeENWNVlSejNnT0dXbzdWb2FPT20wYnRVZXN2cUxHMFdua25IOFRrYTV4OWFUZjdmY0lCeUpRK0I2eGFJWlowdmZaWGU3UUhDRk95THl5RndrVDFUYWxmR25uWjJYclNuUHV2cU5OVFVaaHlBMTZ5VVI1M2Qva3U5MVBBL1JkOFIyNkhsTGFjOXY0emJQU1RiV1RBWlVsT2I3UVZBRDRzY3IrSVV2T3F6SmF4ZHdaMmFsS0JyUmRGSTA4enFJa1JkSmo1RkQ3Nm5CcWlUNzhQVFBOYUhwL3p1V2wrclFZd1JyVTJFT3M4Y2dkZmVkamJBRExBYVJsMFNuZW1qSWltSWZqZnpTcm5TRUxFWDdtQmZ1QitiNlZiS0NMM1FWR0J4TlQwZ2lxczFBRm91bG0rQjc3R0hjOSs3WXlsMElHTjcyMUtWbytxQUNUR3VPNDRNQkR0VXBxemZ2YjU2VVNTeHFLUjk4R2FWUU9kRUNiQUlHVytNVWpGSDMyZnpLb0IzTyt4VmJDamt4cWg4aEpMclNjUWNXZHdiRkFXTElIUFAxRU5jSU1IUWF1N1pRRTZFTWdTUGg0V0ZLTWxxVzViYS9BS0QzZDJxSlJyUjR6TFJrUy9jTW8yN3NRLytlUnlVSTVkc1NJUUY1cTREeEthaHZocDZzVEpuM1MxaG1kN0cvakU2YWF6UFltRXNXRnhJc09teXlseVdLSDZCajErd2N1cWlEcCs5MS80Mi9rdTgzNGtGZTRWcWVqQk5xUnNqYWhKZS9wdHBLMUFyUFh3Z3lJZjRnSDlSQ1RMTXVXWERmcUNEU2licGxzelBhaHJOTUc1YVlsaXgvc2lkSUR5dEZuYVQ3Y3EmdXFHS1c2cFBLcUlucjA0WkV1V3l2YUM0UTY4PQ==; __Secure-s_a=UEpPdElXZlErMUpMbUlFRHVncnM0NHhJc3NtRjcvL2RlVzRsM01YWE9Gam5sSzJ1cGE2SXJZd3JQQ3ZxeTJ1WjVCZlB1cXdHTEIrZ01FTy96RWtNdnAwRXZWNjlnYis3WHA5cnMzU3ZVWVFzMThPS3NITkV1M0hSbStzc3oxeVQ4Zng4NmgvNWhZbmkzNHc2YWJWSWlMbjNwZ2JCcUE2OTNNSi9hYWEwR1EyNnNTU1l5QU9kTnhqc1BPaVhoTEZnYm1WM2F5TXVXbERCY2R0TWwvOFlHd1ZqaWpZejUxRElvcDN5RzE2ejVUMVBUR2NvM0NQbEthS0hWNGlkSVpjZVpxZ1pwRDZBWjl1NHV2SW9xYjUzdnBJZHErQzdGV1htdEVHV04vd3pnQk9ON05xZkVPSXBoWEh1T2M4V0V3c05lZ1hVVUx3WHJxQ1dzalFGSlNRNU1HT012bk1QU1UyeC8rOFJTc3F0U1cyc3YyUW1mME1pN2IyTWNDcFNjbTFFMTdINGFIQlFnd1U0TDFhdDZzVG1tZmdCMmtPRVp2TGhkRHRYam5lUDhjbmM4OGw4UWlkTEZDUGIyZFdJQUltMjJ3amFlT1VSY2Q3Q05ET1VJVTRBazM3TGFxbXpUYXY4aGdYaVkvVVpWWS9vUWluNzZjQzBiMG1EdUJtd3lxcHRkV29iWmxWWDBFbHhKSjFpQmxBVGZPOGwydnRHbTVmMTUzWWdFaW1OVFl6c21sVmo5cXNYQ1VQWkxnbTZHdmhlcEFyTi9Kai9XbEFiRnh0SEZtNndxdTViYjFRam02YVRYRkViRUhoSVNESTVKb2FPR0xuUEVuVmR3bEIxcEU4anBHRlpLMGRUbzUxZHNhblRJOWdEV2VBVmxHbFkrV25hb2Zka21pWFE5Zk4yWlU5QzlRNWFUOWlQTlNnbDVNcHlRSHR4L3lXSFdKTU9lVDVoazBFaW05N2N4VG8zVmJuQVBOVmR5SE44Zyt5cUNVK1pVRmhVMVArRTdZU3d3UDV5eHQ5RlJFRGxTakdKM2U2MGp2WUZoM1JNa1dtdk96RkU4K3YwZkFVcDBiSzh2RlR4Mm5QQWc2TlI4YXdOaDl0RkJkU3ZWVUVEMTNkRnNDT2tibVJYRXNRTG9odmU0L0w5TzUzU0VqeFNWdFJUVHRpREJwVndtLzB6OG9JVUo1RXorNWVsWWlVUFd4K21nZmZOaDd5cUpxVjFkaDA4WldvbVhpQjkwcjlYK1FQNnVHR3p3Z3BIYVdqUW1EbXZLc3B2YTAwY0RUNzNZY1hWZ1dPc09lbHREdlF3OVltU1dOT1lzd1FnQ3lvbkVDZz0mU28yMWJJdGNVTmFSanNrUlhpSlRWZllGQTBjPQ==; _b="AYfYZ+l4jd5M65FWgISue0hOWIiuVXgmNcykg/Pjx7UAzqIIvQGJTmsTBBgAIp2doPU="; cm_sub=allowed; ar_debug=1; _routing_id="e37187f2-d86d-4b8b-a644-8c2919354068"; sessionFunnelEventLogged=1')
            )
            page = context.new_page()

            # 访问搜索页面
            url = f"https://www.pinterest.com/search/pins/?q={name}"
            page.goto(url)
            print(f"访问页面: {url}")

            # 等待页面加载
            # page.wait_for_load_state("networkidle")

            # 追踪已爬取的项目URL避免重复
            projects = []
            seen_urls = set()

            # 设置项目计数器显示爬取进度
            count = 0
            print(f"开始爬取，目标数量: {max_projects} 个项目")

            while count < max_projects:
                time.sleep(scroll_delay)
                # 等待至少一个图片元素可见
                page.wait_for_selector("div.XiG.zI7.iyn.Hsu img", state="visible", timeout=30000)

                # 使用更完整的选择器
                links = page.query_selector_all("div.XiG.zI7.iyn.Hsu img")
                print(f"当前页面上找到 {len(links)} 个项目")
                # print()
                # 处理新发现的链接
                new_found = False

                # print(links)
                for link in links:
                    srcset = link.get_attribute("srcset")
                    # print(f"srcset: {srcset}")
                    high_res_url = None
                    # 解析srcset提取4x分辨率URL
                    if srcset:
                        srcset_parts = srcset.split(", ")
                        # print(srcset_parts)
                        for part in srcset_parts:
                            if "originals" in part:
                                # 提取URL（移除尾部的4x标识符）
                                high_res_url = part.split(" ")[0]
                                # high_res_images.append(high_res_url)

                        if not high_res_url or high_res_url in seen_urls:
                            continue
                    else:
                        continue
                    #
                    count += 1
                    print(f"提取到原始尺寸(4x)图片: {high_res_url}")
                    projects.append({
                        "title": name,
                        "detail_url": high_res_url,
                        "author": "未知",
                        "author_url": "",
                        "likes": 0,
                        "views": 0,
                        "search": name,
                        "platform": "pinterest"
                    })
                    seen_urls.add(high_res_url)
                    new_found = True

                    print(f"[{count}/{max_projects}]  找到项目: {high_res_url}")
                    #
                    #         #         # 如果达到目标数量，退出循环
                    if count >= max_projects:
                        break
                #
                #     # 如果达到目标数量，退出最外层循环
                if count >= max_projects:
                    break
                    # 如果没有找到新链接但还未达到目标数量，尝试滚动加载更多
                if not new_found and count < max_projects:
                    print(f"滚动加载更多内容... 当前: {count}/{max_projects}")
                    # 滚动到页面底部
                    page.evaluate("""
                         window.scrollTo(0, document.body.scrollHeight);
                         window.dispatchEvent(new Event('scroll'));
                         """)
                    # 等待内容加载
                    time.sleep(scroll_delay)

                    # 检查是否还有更多内容可加载
                    retry_count = 0
                    scroll_again = True

                    while retry_count < 5 and not new_found and scroll_again:

                        before_scroll = page.evaluate("() => window.pageYOffset")
                        page.evaluate("""
                             window.scrollTo(0, document.body.scrollHeight);
                             window.dispatchEvent(new Event('scroll'));
                             """)
                        time.sleep(1)
                        after_scroll = page.evaluate("() => window.pageYOffset")
                        print(f"滚动前位置: {before_scroll}, 滚动后位置: {after_scroll}")

                        time.sleep(scroll_delay)

                        # 检查是否加载了新内容
                        current_links_count = len(seen_urls)
                        # 等待至少一个图片元素可见
                        page.wait_for_selector("div.XiG.zI7.iyn.Hsu img", state="visible", timeout=30000)

                        # 使用更完整的选择器
                        links = page.query_selector_all("div.XiG.zI7.iyn.Hsu img")
                        for link in links:
                            srcset = link.get_attribute("srcset")

                            # 解析srcset提取4x分辨率URL
                            if srcset:
                                srcset_parts = srcset.split(", ")
                                for part in srcset_parts:
                                    if "originals" in part:
                                        # 提取URL（移除尾部的4x标识符）
                                        high_res_url = part.split(" ")[0]
                                        # high_res_images.append(high_res_url)
                                        print(f"提取到原始尺寸(4x)图片: {high_res_url}")
                            if high_res_url and high_res_url not in seen_urls:
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
            project_urls = [project['detail_url'] for project in projects]

            return projects, project_urls
        finally:
            # 确保无论如何都关闭浏览器，释放资源
            if browser:
                browser.close()


def chunk_list(lst, n):
    """将列表 lst 分成多个子列表，每个子列表最多包含 n 个元素"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def inster_word(data):
    # try:
    insert_query = """
       INSERT  INTO `work` (`portfolio_uid`, `image_url`, `tags`) 
       VALUES (%s, %s, %s)

       """

    data_values = (
        data['portfolio_uid'],
        data['image_url'][0],
        data['tags'],

    )
    cursor.execute(insert_query, data_values)
    conn.commit()


def scrape_behance_details(urls: list[tuple | Any], proxy=None, name: str = None):
    # url_chunks = chunk_list(urls, 20)
    #
    #
    for url in urls:
        image_paths = down_imgs([url[0]], proxy, name)
        # # 每一批插一次
        data = {
            "portfolio_uid": url[1],
            "image_url": image_paths,
            "tags": url[2]
        }
        inster_word(data)
        upadate_portfolio(url[1])

    return 0


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
    image_paths = []
    for img in imgs:
        t = threading.Thread(target=tps, args=(img, proxy, name, image_paths))
        threadings.append(t)
        t.start()

    for x in threadings:
        x.join()

    print(f"多线程下载图片完成!")
    return image_paths


def tps(img_url, proxy=None, name=None, image_paths=None):
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
    img_path = os.path.abspath(f'{name_os}/{img_name}')  # 获取绝对路径
    with open(img_path, 'wb') as f:
        f.write(r.content)
    print(f">> {img_name}下载图片成功")
    if image_paths is not None:
        image_paths.append(img_path)  # 将绝对路径添加到列表中


def main():
    proxy = {
        "server": "http://10.7.100.40:9910"
    }
    # 第一步：抓取项目列表
    projects, project_urls = scrape_behance_projects(max_projects=1000, proxy=proxy, name="Cadillac")
    uid_list = inster_data(projects)

    if uid_list == []:
        print("没有新作品集需要下载")
        return
    # 使用参数化查询来避免SQL注入
    placeholders = ', '.join(['%s'] * len(uid_list))
    sql = f"""
    select    `detail_url`,`uid`,`title`  from portfolio where uid in ({placeholders}) and is_pick=0;

    """
    cursor.execute(sql, uid_list)  # 执行语句
    # sql = f"""
    # select    `detail_url`,`uid`,`title`  from portfolio where title='Cadillac' and is_pick=0 and platform='pinterest' limit 5;
    #
    # """
    # cursor.execute(sql)  # 执行语句
    data_list = cursor.fetchall()  # 通过fetchall方法获得数据

    # 第二步：抓取项目详情和图片
    scrape_behance_details(data_list, proxy=proxy, name="cadillac")

    print("任务完成!")


main()
