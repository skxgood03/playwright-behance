import requests
from bs4 import BeautifulSoup
import time
import random


def search_dribbble_pages(name, start_page=1, end_page=1, cookie=None):
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
        results = search_dribbble(name, page=page, cookie=cookie)
        all_results.extend(results)

        # 添加随机延迟，防止请求过于频繁
        if page < end_page:
            delay = random.uniform(1, 3)
            print(f"等待 {delay:.2f} 秒后继续...")
            time.sleep(delay)

    return all_results


def search_dribbble(name, page=1, per_page=24, cookie=None):
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

    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # 如果提供了cookie，添加到headers中
    if cookie:
        headers['Cookie'] = cookie

    try:
        # 发送请求
        response = requests.get(url, headers=headers)
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


# 使用示例
if __name__ == "__main__":
    # cookie字符串
    cookie = """anonymous_id=bdd3c0f4-938b-474b-9b58-50cb38d53e6a; cookieyes-consent=consentid:WlJVdVVLSEpVWk9WN3dOaVBIR1dKZzdzcXdyTWExeVA,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; split=%7B%22shot_search_20250318%22%3A%22pointguard%22%7D; user_session_token=2b7784b9-fbb7-44d0-9b2c-d3bbbf90ebff; has_logged_in=true; _ga_HCEJXK4TN5=GS1.1.1744960481.1.1.1744960988.60.0.0; __stripe_mid=55466ddc-c178-409f-8e68-1b5d6f67f4210d13bd; _ga_0ZEY8QS3T8=GS1.1.1744960482.1.1.1744960996.52.0.0; _gid=GA1.2.1664181898.1745204207; _ga_25KD9QBT3M=GS1.1.1745222509.4.1.1745223190.0.0.0; _ga_Y7FZW1KKL0=GS1.1.1745226420.4.0.1745226420.0.0.0; __stripe_sid=9935621c-bfb8-4f15-93a8-7a661ea9ae61c21576; _ga=GA1.1.103624395.1744357742; _ga_YY4DGM66J9=GS1.1.1745226644.1.1.1745226644.0.0.0; _ga_ZMZQ0G7RSZ=GS1.1.1745226646.1.0.1745226646.60.0.0; _ga_KS7YMK0S14=GS1.1.1745226647.1.0.1745226647.0.0.0; _dribbble_session=IUmvs%2B%2B29By2gg7W5B945CWuTm57auigtr%2Fib23%2FmxOaH0GtIovVnvnvtFhNHN8j%2BzvdHtv9G5xZN8dywB%2BRmzG76g%2B2D9L7bAnW4aKEJQlabTrvCCh57hdUPRZ%2F7lRzXaABYFQT%2BeAnTnEFmMqaj3w5RUBkjXnHZjK94pb3b1%2F5alYEnUbFtoo1JnYpcJ7DcW0KIKo8PA80XniEQA9qXaeMw4EdAHJTq9NxKVGG49iEjv24oOViPhM4RZ4p0rvr1LvQ883J9lz4%2F8yovNYI3FXiOLr3ar2xo1l0L%2BLVOq5BD%2FIdRMsJgSwsc%2Bi0T%2BJFW6gazhkK8%2B7JJKVJ5fjl%2BC76drpHm%2FYGvPzY0K5WJFdh%2BUrDvMiIRbgX7UbuZPlHKt8JJ9XLSj1sRXWLEJlpmbWQ0ctzeLZeDyGi248HaWq0e6AlcyrLT2Z%2FVFIhp5Z%2F5sFqUlygjjsPPZZr2t7GUx0%2BZNYTLjkT%2FZGISk9%2F4BxGoS9H1AdRcy3TqOAth8pqZ6L9SGVovGJw62ZyuKBIsDH8ARfBXsh4Qyi5Kv9T89K0--EU4PiGa0K60%2BMvPP--fj0wqnRdocQTF2%2FL3fDh0g%3D%3D; _ga_EV4S8HEMZG=GS1.1.1745226433.5.1.1745226667.0.0.0; _ga_PDGJMQ62L7=GS1.1.1745226433.5.1.1745226667.0.0.0; _gcl_au=1.1.1717099434.1744357743.291369462.1745226646.1745226667"""

    # 调用多页搜索函数，这里爬取第1页到第10页
    results = search_dribbble_pages("cadillac", start_page=1, end_page=10, cookie=cookie)

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