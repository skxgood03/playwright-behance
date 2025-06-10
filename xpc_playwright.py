from playwright.sync_api import sync_playwright
import time


def parse_cookies(cookie_string):
    """解析cookie字符串为列表字典格式"""
    cookies = []
    for cookie in cookie_string.split(';'):
        if '=' in cookie:
            name, value = cookie.strip().split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.xinpianchang.com',
                'path': '/'
            })
    return cookies


def automate_video_quality():
    cookie_str = """Device_ID=34m0keet6ma0hqi6c; Authorization=6268231C6E27143FB6E27140C16E2719F096E271AC4C70719AE5; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2215485965%22%2C%22first_id%22%3A%221967a56b2b22558-0007ddb9e842dcac-26011c51-1639680-1967a56b2b32e09%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%221967a56b2b22558-0007ddb9e842dcac-26011c51-1639680-1967a56b2b32e09%22%7D; Hm_lvt_446567e1546b322b726d54ed9b5ad346=1746508491,1746519419,1746588289,1746686509; HMACCOUNT=1DD332A351373D93; Hm_lpvt_446567e1546b322b726d54ed9b5ad346=1746769734"""

    with sync_playwright() as p:
        # 设置浏览器启动参数
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )

        # 创建新的上下文并设置详细的参数
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        )

        page = context.new_page()

        try:
            # 设置更长的超时时间
            page.set_default_timeout(60000)  # 设置为60秒

            # 首先访问网站以设置cookies
            page.goto("https://www.xinpianchang.com")

            # 设置cookies
            cookies = parse_cookies(cookie_str)
            context.add_cookies(cookies)

            # 访问目标页面并等待加载
            page.goto("https://www.xinpianchang.com/a13119075", wait_until="networkidle")

            # 等待视频元素出现
            page.wait_for_selector("video", state="attached", timeout=60000)

            # 注入JavaScript来检查video元素
            video_exists = page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    return video && video.getAttribute('src');
                }
            """)

            if not video_exists:
                raise Exception("Video element not found or src attribute is missing")

            # 获取视频src
            video_element = page.locator("video")
            video_src = video_element.get_attribute("src")
            print(f"Video source URL: {video_src}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # 保存页面截图以便调试
            page.screenshot(path="error_screenshot.png")
            # 保存页面内容以便调试
            with open("page_content.html", "w", encoding="utf-8") as f:
                f.write(page.content())

        finally:
            browser.close()


if __name__ == "__main__":
    automate_video_quality()