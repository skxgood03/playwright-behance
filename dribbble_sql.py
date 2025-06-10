import math
import os
import threading

import requests
from bs4 import BeautifulSoup
import time
import random

from playwright_behance_sql import upadate_portfolio, inster_data
from db.db_config import conn

cursor = conn.cursor()


def search_dribbble_pages(name, start_page=1, end_page=1, cookie=None, max_projects=None, proxy=None):
    """
    搜索多页Dribbble图片

    Args:
        name: 搜索关键词
        start_page: 起始页码
        end_page: 结束页码
        cookie: Cookie字符串

    Returns:
        list: 所有页面的搜索结果列表
    """
    all_results = []

    for page in range(start_page, end_page + 1):
        print(f"正在抓取第 {page} 页...")
        # 获取当前页的结果
        results = search_dribbble(name, page=page, cookie=cookie, proxy=proxy)
        print(f"第 {page} 页获取到 {len(results)} 条结果")
        if len(results) == 0:
            print(f"第 {page} 页没有结果，停止爬取。")
            break
        all_results.extend(results)
        # 如果已达到最大项目数，停止爬取
        if len(all_results) >= max_projects:
            return all_results[:max_projects]

        # 添加随机延迟，防止请求过于频繁
        if page < end_page:
            delay = random.uniform(1, 3)
            print(f"等待 {delay:.2f} 秒后继续...")
            time.sleep(delay)

    return all_results[:max_projects]


def search_dribbble(name, page=1, per_page=24, cookie=None, proxy=None):
    """
    搜索单页Dribbble图片

    Args:
        name: 搜索关键词
        page: 页码
        per_page: 每页数量
        cookie: Cookie字符串

    Returns:
        list: 搜索结果列表
    """
    # 构建URL
    url = f"https://dribbble.com/search/{name}?page={page}&per_page={per_page}"
    print(f"请求URL: {url}")
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # 如果提供了cookie，添加到headers中
    if cookie:
        headers['Cookie'] = cookie

    try:
        # 发送请求
        proxies = {"http": proxy['server'], "https": proxy['server']} if proxy else None
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()

        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 存储结果
        projects = []

        # 查找所有shots
        shots = soup.find_all('li', class_='shot-thumbnail')

        for shot in shots:

            try:
                # 获取标题
                title_elem = shot.find('span', class_='accessibility-text')
                title = title_elem.text.strip().replace('View ', '') if title_elem else ''

                # 获取最佳图片地址
                img_elem = shot.find('img', {'data-srcset': True})
                if img_elem and img_elem.get('data-srcset'):
                    # 从data-srcset中获取最大分辨率的图片URL
                    srcset = img_elem['data-srcset']
                    # 分割srcset并获取最后一个URL（通常是最大分辨率）
                    urls = [url.split(' ')[0] for url in srcset.split(', ')]
                    detail_url = urls[-1] if urls else ''
                else:
                    detail_url = ''

                # 获取作者信息
                author_elem = shot.find('span', class_='display-name')
                author_name = author_elem.text.strip() if author_elem else ''

                # 获取点赞数
                likes_elem = shot.find('span', class_='js-shot-likes-count')
                likes = likes_elem.text.strip() if likes_elem else '0'
                # 清理数字
                likes = ''.join(filter(str.isdigit, likes))

                # 获取浏览量
                views_elem = shot.find('span', class_='js-shot-views-count')
                views = views_elem.text.strip() if views_elem else '0'
                # 处理k单位
                views = views.strip().lower()
                if 'k' in views:
                    # 提取数字部分
                    num = ''.join(filter(lambda x: x.isdigit() or x == '.', views))
                    views = str(int(float(num) * 1000))
                else:
                    # 如果没有k，直接提取数字
                    views = ''.join(filter(str.isdigit, views))

                # 添加到结果列表
                projects.append({
                    "title": title,
                    "detail_url": detail_url,
                    "author": author_name,
                    "author_url": "",
                    "likes": likes,
                    "views": views,
                    "search": name,
                    "platform": "dribbble"
                })

            except Exception as e:
                print(f"解析单个shot时出错: {str(e)}")
                continue

        return projects

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {str(e)}")
        return []
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return []


def inster_word(data):
    # try:
    insert_query = """
       INSERT  INTO `work` (`portfolio_uid`, `image_url`, `tags`) 
       VALUES (%s, %s, %s)

       """

    data_values = (
        data['portfolio_uid'],
        data['image_url'],
        data['tags'],

    )
    cursor.execute(insert_query, data_values)
    conn.commit()


def scrape_details(data_list, name, proxy=None):
    image_paths = down_imgs(data_list, name, proxy)
    for image in image_paths:
        inster_word(image)
        upadate_portfolio(image['portfolio_uid'])

    print(image_paths)


def down_imgs(data_list, name, proxy=None, max_threads=10):
    threadings = []
    image_paths = []
    # 创建信号量，限制最大线程数为10
    semaphore = threading.Semaphore(max_threads)

    def download_with_semaphore(obj, name, image_paths, proxy):
        # 获取信号量
        with semaphore:
            tps(obj, name, image_paths, proxy)

    for obj in data_list:
        if obj[0] == "":
            continue
        t = threading.Thread(target=download_with_semaphore,
                             args=(obj, name, image_paths, proxy))
        threadings.append(t)
        t.start()

    for x in threadings:
        x.join()

    print(f"多线程下载图片完成!")
    return image_paths


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


def tps(obj, name, image_paths=None, proxy=None):
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
    img_name = obj[0].split('/')[-1]
    img_name = img_name.split("?")[0]
    print(img_name)
    r = get_response(obj[0], headers, proxy)
    time.sleep(1)
    name_os = name.replace(" ", "")
    os.makedirs(name_os, exist_ok=True)
    img_path = os.path.abspath(f'{name_os}/{img_name}')  # 获取绝对路径
    with open(img_path, 'wb') as f:
        f.write(r.content)
    print(f">> {img_name}下载图片成功")
    if image_paths is not None:
        image_paths.append({"image_url": img_path, "portfolio_uid": obj[1], "tags": name})  # 将绝对路径添加到列表中
    print(f">> {img_name}下载图片成功")


def main(max_projects: int = 24, name: str = "chery tiggo9", cookies=None):
    proxy = {
        "server": "http://10.7.100.40:9910"
    }
    # cookie字符串
    # cookie = """anonymous_id=bdd3c0f4-938b-474b-9b58-50cb38d53e6a; cookieyes-consent=consentid:WlJVdVVLSEpVWk9WN3dOaVBIR1dKZzdzcXdyTWExeVA,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; split=%7B%22shot_search_20250318%22%3A%22pointguard%22%7D; user_session_token=2b7784b9-fbb7-44d0-9b2c-d3bbbf90ebff; has_logged_in=true; _ga_HCEJXK4TN5=GS1.1.1744960481.1.1.1744960988.60.0.0; __stripe_mid=55466ddc-c178-409f-8e68-1b5d6f67f4210d13bd; _ga_0ZEY8QS3T8=GS1.1.1744960482.1.1.1744960996.52.0.0; _gid=GA1.2.1664181898.1745204207; _ga_25KD9QBT3M=GS1.1.1745222509.4.1.1745223190.0.0.0; _ga_Y7FZW1KKL0=GS1.1.1745226420.4.0.1745226420.0.0.0; __stripe_sid=9935621c-bfb8-4f15-93a8-7a661ea9ae61c21576; _ga=GA1.1.103624395.1744357742; _ga_YY4DGM66J9=GS1.1.1745226644.1.1.1745226644.0.0.0; _ga_ZMZQ0G7RSZ=GS1.1.1745226646.1.0.1745226646.60.0.0; _ga_KS7YMK0S14=GS1.1.1745226647.1.0.1745226647.0.0.0; _dribbble_session=IUmvs%2B%2B29By2gg7W5B945CWuTm57auigtr%2Fib23%2FmxOaH0GtIovVnvnvtFhNHN8j%2BzvdHtv9G5xZN8dywB%2BRmzG76g%2B2D9L7bAnW4aKEJQlabTrvCCh57hdUPRZ%2F7lRzXaABYFQT%2BeAnTnEFmMqaj3w5RUBkjXnHZjK94pb3b1%2F5alYEnUbFtoo1JnYpcJ7DcW0KIKo8PA80XniEQA9qXaeMw4EdAHJTq9NxKVGG49iEjv24oOViPhM4RZ4p0rvr1LvQ883J9lz4%2F8yovNYI3FXiOLr3ar2xo1l0L%2BLVOq5BD%2FIdRMsJgSwsc%2Bi0T%2BJFW6gazhkK8%2B7JJKVJ5fjl%2BC76drpHm%2FYGvPzY0K5WJFdh%2BUrDvMiIRbgX7UbuZPlHKt8JJ9XLSj1sRXWLEJlpmbWQ0ctzeLZeDyGi248HaWq0e6AlcyrLT2Z%2FVFIhp5Z%2F5sFqUlygjjsPPZZr2t7GUx0%2BZNYTLjkT%2FZGISk9%2F4BxGoS9H1AdRcy3TqOAth8pqZ6L9SGVovGJw62ZyuKBIsDH8ARfBXsh4Qyi5Kv9T89K0--EU4PiGa0K60%2BMvPP--fj0wqnRdocQTF2%2FL3fDh0g%3D%3D; _ga_EV4S8HEMZG=GS1.1.1745226433.5.1.1745226667.0.0.0; _ga_PDGJMQ62L7=GS1.1.1745226433.5.1.1745226667.0.0.0; _gcl_au=1.1.1717099434.1744357743.291369462.1745226646.1745226667"""
    end_page = math.ceil(max_projects / 24)
    print(f"每页最多获取 {max_projects} 条数据，最多获取 {end_page} 页数据")
    # 调用多页搜索函数，这里爬取第1页到第10页
    results = search_dribbble_pages(name, start_page=1, end_page=end_page, cookie=cookies, max_projects=max_projects,
                                    proxy=proxy)

    # 打印总结果数量
    print(f"\n总共获取到 {len(results)} 条结果")

    # 打印每条结果
    for i, result in enumerate(results, 1):
        print(f"\n--- 结果 {i} ---")
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']}")
        print(f"点赞数: {result['likes']}")
        print(f"浏览量: {result['views']}")
        print(f"图片URL: {result['detail_url']}")
    uid_list = inster_data(results)

    if uid_list == []:
        print("没有新作品集需要下载")
        return
    # 使用参数化查询来避免SQL注入
    placeholders = ', '.join(['%s'] * len(uid_list))
    sql = f"""
        select    `detail_url`,`uid`,`title`  from portfolio where uid in ({placeholders}) and is_pick=0;

        """
    cursor.execute(sql, uid_list)  # 执行语句

    data_list = cursor.fetchall()  # 通过fetchall方法获得数据

    # 第二步：抓取项目详情和图片
    scrape_details(data_list, name, proxy)

    print("任务完成!")


main(max_projects=1000)
