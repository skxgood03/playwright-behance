import json
import os
import random
import threading
import time
from typing import Any

import requests
from playwright.sync_api import sync_playwright


def get_cookies(cookies: str):
    # 提供的cookie字符串
    cookie_string = cookies

    # 解析cookie字符串为字典列表
    cookies = []
    for cookie_pair in cookie_string.split('; '):
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            # 针对不同域名的cookie使用不同的domain设置
            if 'passport' in name:
                domain = '.douyin.com'  # passport相关的cookie通常是在主域名下
            else:
                domain = '.douyin.com'  # 默认使用主域名

            cookies.append({
                'name': name,
                'value': value,
                'domain': domain,
                'path': '/',
                'secure': True,  # 对于抖音/字节跳动的网站，建议设置secure
                'httpOnly': True if any(x in name for x in ['sid', 'sessionid', 'passport', 'auth']) else False
                # 一些敏感cookie通常是httpOnly的
            })
    return cookies

def scrape_xhs_projects():


    with sync_playwright() as p:
        browser = None
        try:
            # 启动浏览器
            browser = p.chromium.launch(headless=False)
            context_options = {"viewport": {"width": 1920, "height": 1080}}

            # 设置cookies
            context = browser.new_context(**context_options)
            context.add_cookies(get_cookies(
                'gfkadpd=2906,33638; __security_mc_1_s_sdk_crypt_sdk=1bbcadf2-4df4-a240; __security_mc_1_s_sdk_cert_key=9b22380f-48af-9756; _security_mc_1_s_sdk_sign_data_key_web_protect=0d4df504-4bee-8288; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQnBQNnU3Y1RFR3pVbzN6M1ZyUDU2MUkrdDdrc3RVZDNJNXFWMUtnK1Vna2VYRkdkS0QwWi9VVDB4WGhqZ1lqQ1hmRGphYXBVaDZKMjZOa0FJV0dKQTA9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_web_domain=2; ttwid=1%7CMWsC4xhMEzyQH8ZyaB785VCJF3DJ4XUH8D4TkfQCJcM%7C1744783966%7Cd29dc55548a6f998446b895f1401445fafdcc51b9f64af8789a223d62ec6f1e3; biz_trace_id=d3f1459a; passport_csrf_token=d68e876eae1156fd2fbcd5a15e9e734b; passport_csrf_token_default=d68e876eae1156fd2fbcd5a15e9e734b; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e5827292771273f273d343d33333c363d32313132342778; bit_env=OuO9ZkNVm9teJRCwyQke_X0vQ67FzzATweXYHE2Hlw0vcprH1q8RyxRF1U7-mA51s-5bOptZRaUpmXeHgONCNZwgkKy8VBjqgacqbiRIghrdCGsRag-N6FSuvuB2rR41zfxg5uUs8m4c6dN_5D-g0qfBdDp8KMwzVsJKXqtq_2iKxYC3z65a_lecnnkKR8a_hZSEYoJWQT4xNcfeDdqFudK2wzHGLpliIxNsmirpH1p1JUzu1d-ez15W1skWb1spTRLr7ehzT_f0q0vbWweELAXHBIJBtEalBJNI8LaCHSiGoquIBTIZc43KcUfWt_3YeRU3_X9V1nQ3pRP8CzXpbqPNFJXJgiQVzea1XQMZbqWAnWACGTvZ7gqjLcOrSet8mnCia7ghLojgnYdsyJ-tPiDI4giAFyCDxzDtglumvh5UI7uJa6k6U5YWoaIBN9kU13IOuwaU-Q3LyINM28kABJIrxnSw0FiGiZ2eKzDe4-FKfhiqLaFX369LjK-XXToHv2ZCTgRgEJ_JUjMF4m0FdeCQbGN4gkaR1pnoVvNdvU%3D; gulu_source_res=eyJwX2luIjoiMGU3MGQ5NWQwMTU1ZDhkZmFkYTIwODJlZThmZmQ1ZWE5MGZmNThkMjMyMDlhM2QyMTFjMmNlZTY3ZTM2OWJmNyJ9; passport_auth_mix_state=dpqa8f5ltakadnmzms80g9qu5pzw7gvb0gup18tzxf8cgwky; odin_tt=6882e3d2ff4ce6260add95605495a511cf0d938e4afb3aa99c574d916069839a797ca23156ea3c562ae803cf0fbe802c; passport_assist_user=CjyEfJhoIkuF6edMQUjXwYtoglszFuvwzAH8wMzWCcEubAUkUyUOK_ZLBVmGg483h-XPcncTFtkb_GslkfAaSgo8AAAAAAAAAAAAAE7iRVyGmlM9cm1-cnDZ67QuKjApczlBd9A_RMr5w4taInUuwdzQ5xS5inrHdw0M4MRaEInw7g0Yia_WVCABIgEDuMfOcA%3D%3D; n_mh=aCx1OtXVI0dkZMtIE8DLzjFl204zfFMrk4WLv04069I; sid_guard=36af98ea8b165063a5d5a85207acb346%7C1744783986%7C5184000%7CSun%2C+15-Jun-2025+06%3A13%3A06+GMT; uid_tt=afc7126d3efb18cf39b38d00269d5e4f; uid_tt_ss=afc7126d3efb18cf39b38d00269d5e4f; sid_tt=36af98ea8b165063a5d5a85207acb346; sessionid=36af98ea8b165063a5d5a85207acb346; sessionid_ss=36af98ea8b165063a5d5a85207acb346; is_staff_user=false; sid_ucp_v1=1.0.0-KDdmNDgzOGQzYzZlYjMwMzE3Y2YxNDc0ZDE3ZTY1NWI5MjEwMjFmMGQKHwioo7KAxAEQ8pT9vwYY2hYgDDCE5YnCBTgHQPQHSAQaAmxmIiAzNmFmOThlYThiMTY1MDYzYTVkNWE4NTIwN2FjYjM0Ng; ssid_ucp_v1=1.0.0-KDdmNDgzOGQzYzZlYjMwMzE3Y2YxNDc0ZDE3ZTY1NWI5MjEwMjFmMGQKHwioo7KAxAEQ8pT9vwYY2hYgDDCE5YnCBTgHQPQHSAQaAmxmIiAzNmFmOThlYThiMTY1MDYzYTVkNWE4NTIwN2FjYjM0Ng; bd_ticket_guard_server_data=eyJ0aWNrZXQiOiJoYXNoLms4aHpPNEdFZEZheHNrVnY0SXIxdjlLMThYZkFuSEVDQVhPZVR3ekdub289IiwidHNfc2lnbiI6InRzLjIuZTg5NDE0MWU4OWJiZTllMjg0ZDVlOTM0NDRlNzY4OGRhZTc2ZTk3ZDQyZmZlZWZjZDJmZmNjZmU3NzExOGE3NGM0ZmJlODdkMjMxOWNmMDUzMTg2MjRjZWRhMTQ5MTFjYTQwNmRlZGJlYmVkZGIyZTMwZmNlOGQ0ZmEwMjU3NWQiLCJjbGllbnRfY2VydCI6InB1Yi5CQnBQNnU3Y1RFR3pVbzN6M1ZyUDU2MUkrdDdrc3RVZDNJNXFWMUtnK1Vna2VYRkdkS0QwWi9VVDB4WGhqZ1lqQ1hmRGphYXBVaDZKMjZOa0FJV0dKQTA9IiwibG9nX2lkIjoiMjAyNTA0MTYxNDEzMDUxRjc1NDEwOEEzN0Y1NDAwRTE3RSIsImNyZWF0ZV90aW1lIjoxNzQ0NzgzOTg2fQ%3D%3D; bd_ticket_guard_web_domain=2; _tea_utm_cache_2906=undefined')
            )
            page = context.new_page()

            # 访问搜索页面
            url = f"https://creator.douyin.com/creator-micro/data-center/operation"
            page.goto(url)
            print(f"访问页面: {url}")

            # 等待页面加载
            page.wait_for_load_state("networkidle")

            value = page.locator("span.blobMetric-WOTeI4 span").text_content()
            print(value)
            time.sleep(10)
        finally:
            # 确保无论如何都关闭浏览器，释放资源
            if browser:
                browser.close()


def main():
    # 确保下载目录存在
    os.makedirs('old', exist_ok=True)
    # 第一步：抓取项目列表
    scrape_xhs_projects()

    print("任务完成!")


main()
