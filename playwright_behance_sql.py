import json
import os
import random
import threading
import time
import uuid
from typing import Any

import requests
from playwright.sync_api import sync_playwright
from db.db_config import conn

cursor = conn.cursor()


def inster_data(data_list):
    # 将 m_id设置唯一索引 使用 INSERT IGNORE(重复数据忽略) 或者 ON DUPLICATE KEY UPDATE（重复数据更新） 的方式插入数据，确保在数据重复时不会抛出错误：
    insert_query = """
    INSERT IGNORE INTO `portfolio` (`uid`, `author`, `title`, `detail_url`, `platform`, `likes`,`views`,`author_url`,`search`,`is_pick`) 
    VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s,%s)

    """

    data_values = []
    uid_list = []
    detail_urls = []  # 存储所有detail_url用于后续查询

    for data in data_list:
        uid = str(uuid.uuid4())
        uid_list.append(uid)
        detail_urls.append(data['detail_url'])
        data_values.append((
            uid,
            data['author'],
            data['title'],
            data['detail_url'],
            data['platform'],
            data['likes'],
            data['views'],
            data['author_url'],
            data['search'],
            0
        ))

    # 批量执行插入
    cursor.executemany(insert_query, data_values)
    affected_rows = cursor.rowcount
    conn.commit()

    if affected_rows == len(data_list):
        # 如果所有记录都插入成功，直接返回所有uid
        return uid_list
    else:
        # 查询与传入的detail_urls匹配的所有记录，并且is_pick为0
        placeholders = ', '.join(['%s'] * len(detail_urls))
        query = f"""
        SELECT uid FROM portfolio 
        WHERE detail_url IN ({placeholders}) AND is_pick = 0
        """

        cursor.execute(query, detail_urls)

        # 获取所有符合条件的UID
        uids_to_return = [row[0] for row in cursor.fetchall()]

        return uids_to_return


def inster_word(data):
    # 从字典中提取值
    portfolio_uid = data['portfolio_uid']
    image_url_list = data['image_url']
    tags = data['tags']
    data_values = []
    # try:
    insert_query = """
       INSERT  INTO `work` (`portfolio_uid`, `image_url`, `tags`) 
       VALUES (%s, %s, %s)

       """
    for image_url in image_url_list:
        data_values.append((
            portfolio_uid,
            image_url,
            tags,

        ))

    cursor.executemany(insert_query, data_values)
    conn.commit()


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
            #     "")
            # )
            page = context.new_page()

            # 访问搜索页面
            url = f"https://www.behance.net/search/projects/{name}?tracking_source=typeahead_nav_recent_suggestion"
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
                project_items = page.locator("div[role='article']").all()
                try:
                    login = page.locator("img.PrimaryNav-avatarImgEl-WDU").first

                    print(login.get_attribute("src"))
                except Exception as e:
                    print("未登录")
                print(f"当前页面上找到 {len(project_items)} 个项目")
                # # 获取当前页面上的所有项目链接
                # links = page.locator("a.ProjectCoverNeue-coverLink-U39").all()
                # print(f"当前页面上找到 {len(links)} 个项目")

                # 处理新发现的链接
                new_found = False

                for project in project_items:
                    # 1. 获取项目详情URL
                    detail_url_element = project.locator("a.ProjectCoverNeue-coverLink-U39")
                    detail_url = detail_url_element.get_attribute("href")

                    # 2. 获取项目标题
                    title_element = project.locator("a.Title-title-lpJ")
                    title = title_element.text_content()

                    # 3. 获取作者名字和链接
                    # 3. 获取作者信息
                    # 先检查是否是多个所有者
                    multiple_owners_element = project.locator("div.Owners-multipleOwnersText-eNJ")

                    if multiple_owners_element.count() > 0:
                        # 对于多个所有者的情况
                        author_name = "多个所有者"
                        author_link = ""
                    else:
                        # 对于单个所有者的情况
                        author_element = project.locator("a.Owners-owner-EEG")
                        if author_element.count() > 0:
                            author_name = author_element.text_content().strip()
                            author_link = author_element.get_attribute("href")

                        else:
                            # 如果找不到作者信息
                            author_name = "未知作者"
                            author_link = ""

                    # 4. 获取点赞数和浏览数
                    stats = project.locator("div.Stats-stats-Q1s span").all()
                    likes = stats[0].text_content() if len(stats) > 0 else "0"
                    views = stats[1].text_content() if len(stats) > 1 else "0"

                    # 处理相对URL
                    if detail_url and detail_url.startswith("/"):
                        href = f"https://www.behance.net{detail_url}"

                    # 跳过已处理的URL
                    if not href or href in seen_urls:
                        continue

                    # # 清理标题
                    # clean_text = clean_title(title)

                    # 保存项目信息
                    projects.append({
                        "title": title,
                        "detail_url": href,
                        "author": author_name,
                        "author_url": author_link,
                        "likes": likes,
                        "views": views,
                        "search": name,
                        "platform": "Behance"
                    })
                    seen_urls.add(href)
                    new_found = True
                    count += 1
                    print(f"[{count}/{max_projects}]  找到项目: {title}")

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
                        # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
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
                        new_links = page.locator("div[role='article']").all()

                        for link in new_links:
                            detail_url_element = link.locator("a.ProjectCoverNeue-coverLink-U39")
                            href = detail_url_element.get_attribute("href")
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
            project_urls = [project['detail_url'] for project in projects]

            return projects, project_urls
        finally:
            # 确保无论如何都关闭浏览器，释放资源
            if browser:
                browser.close()


def upadate_portfolio(param):
    # 更新作品集的is_pick字段为1
    update_query = """
    UPDATE portfolio SET is_pick = 1 WHERE uid = %s
    """
    cursor.execute(update_query, (param,))
    conn.commit()
    print(f"更新作品集 {param} 的is_pick字段为1")


def scrape_behance_details(urls: list[dict | Any], proxy=None, name: str = None, max_retries=3, retry_delay=5):
    """
    爬取Behance项目的详情页，带重试机制

    Args:
        urls: 详情页URL字典
        proxy: 代理设置
        name: 项目名称
        max_retries: 最大重试次数
        retry_delay: 重试间隔时间(秒)
    Returns:
        项目列表，包含标题、链接和ID
    """
    num = 0
    failed_urls = []  # 记录失败的URL

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context_options = {"viewport": {"width": 1920, "height": 1080}}
        if proxy:
            context_options["proxy"] = proxy
        context = browser.new_context(**context_options)
        page = context.new_page()

        for url in urls:
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    num += 1
                    if retry_count > 0:
                        print(f"第 {retry_count} 次重试访问: {url[0]}")
                    else:
                        print(f"正在访问第 {num} 个作品集，详情页: {url[0]}")

                    # 设置页面超时时间
                    page.set_default_timeout(60000)  # 60秒超时

                    # 访问详情页
                    page.goto(url[0], wait_until="networkidle")

                    # 提取图片链接
                    try:
                        # 首先尝试等待图片元素出现
                        page.wait_for_selector("img.ImageElement-image-SRv", timeout=10000)
                        links = page.locator("img.ImageElement-image-SRv").all()
                        tps = page.locator("li.ProjectTags-tag-MKN").all()
                        print(f"当前页面上找到 {len(links)} 个图片")
                        tp_do = ""
                        for tp in tps:
                            # 获取标签链接元素
                            tag_link = tp.locator("a.ProjectTags-tagLink-PxS")
                            # 提取文本内容
                            tag_text = tag_link.text_content().strip()
                            tp_do += tag_text + ","
                        print(tp_do)

                        image_urls = []
                        for link in links:
                            src = link.get_attribute("src")
                            if src:
                                image_urls.append(src)

                        if image_urls:
                            image_paths = down_imgs(image_urls, proxy, name)
                            # 每一批插一次
                            data = {
                                "portfolio_uid": url[1],
                                "image_url": image_paths,
                                "tags": tp_do
                            }
                            inster_word(data)
                            success = True
                            upadate_portfolio(url[1])
                        else:
                            print(f"页面 {url} 没有找到图片")
                            # 即使没有图片也标记为成功，避免无意义重试
                            success = True
                    except Exception as image_error:
                        print(f"提取图片失败: {image_error}")
                        raise  # 向上抛出异常，触发重试

                    # 添加随机延迟以防止被封IP (2-5秒)
                    time.sleep(random.uniform(2, 5))

                except Exception as e:
                    retry_count += 1
                    print(f"处理页面 {url} 时出错: {e}")

                    if retry_count < max_retries:
                        # 计算指数退避时间
                        wait_time = retry_delay * (2 ** (retry_count - 1))
                        wait_time = min(wait_time, 60)  # 最大等待60秒

                        print(f"将在 {wait_time} 秒后重试...")
                        time.sleep(wait_time)

                        # 刷新浏览器上下文以处理可能的会话问题
                        if retry_count == max_retries - 1:
                            print("重新创建浏览器上下文...")
                            context.close()
                            context = browser.new_context(**context_options)
                            page = context.new_page()
                    else:
                        print(f"已达最大重试次数，放弃处理 {url}")
                        failed_urls.append(url[0])

            # 如果处理失败，记录该URL
            if not success:
                failed_urls.append(url[0])

        browser.close()
    print(image_paths)
    # 处理完成后的统计
    total = len(urls)
    success_count = total - len(failed_urls)
    print(f"处理完成! 共 {total} 个URL, 成功: {success_count}, 失败: {len(failed_urls)}")

    # 如果有失败的URL，可以输出到文件
    if failed_urls:
        try:
            with open(f"{name}_failed_urls.txt", "w") as f:
                for furl in failed_urls:
                    f.write(f"{furl}\n")
            print(f"失败的URL已保存至 {name}_failed_urls.txt")
        except Exception as e:
            print(f"保存失败URL时出错: {e}")


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
    print(f">> {img_name}下载图片成功")


def main():
    # 确保下载目录存在
    os.makedirs('old', exist_ok=True)
    proxy = {
        "server": "http://10.7.100.40:9910"
    }
    requests_proxy = proxy['server']
    # 第一步：抓取项目列表
    projects, project_urls = scrape_behance_projects(max_projects=1, proxy=proxy, name="landrover Defender")
    print(projects)
    # 获取本次存入数据库的项目列表
    uid_list = inster_data(projects)
    if uid_list == []:
        print("没有新作品集需要下载")
        return
    # 使用参数化查询来避免SQL注入
    placeholders = ', '.join(['%s'] * len(uid_list))
    sql = f"""
    select    `detail_url`,`uid`  from portfolio where uid in ({placeholders}) and is_pick=0;

    """
    cursor.execute(sql, uid_list)  # 执行语句
    data_list = cursor.fetchall()  # 通过fetchall方法获得数据

    # 第二步：抓取项目详情和图片
    scrape_behance_details(data_list, proxy=proxy, name="landrover Defender")

    print("任务完成!")


main()
