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

            # 根据cookie名称判断domain
            if 'creator' in name:
                domain = 'creator.xiaohongshu.com'
            else:
                domain = '.xiaohongshu.com'

            cookies.append({
                'name': name,
                'value': value,
                'domain': domain,
                'path': '/'
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
                'acw_tc=0a0d096b17447703043421337e04429e5b8dea51278cca40f1ac7bc8e0ba88; xsecappid=ugc; a1=1963c6a0bc5vt0nur3kao199xq6pssgidzrqu17j530000599990; webId=3c4a0bdd472bad25a5b30ff47dbc4118; websectiga=16f444b9ff5e3d7e258b5f7674489196303a0b160e16647c6c2b4dcb609f4134; sec_poison_id=69e290e6-88a9-4fe0-9a97-073717ca81e8; gid=yjKqSK0y2qfSyjKqSK08DuyWS2h98I7FqT0lFV2yjjCAKAq8UMMk378882jjjj88q2ddfKqJ; customer-sso-sid=68c517493731738636414959qcc7albkrniskbka; x-user-id-creator.xiaohongshu.com=6065ecc9000000000101f5ad; customerClientId=272754757510649; access-token-creator.xiaohongshu.com=customer.creator.AT-68c517493731738636414960zidvczqh3ntcvtwn; galaxy_creator_session_id=IXxV6wb5nEQCnmsjEb1yEdLZcAzEUIdonkKZ; galaxy.creator.beaker.session.id=1744770384896050734625')
            )
            page = context.new_page()

            # 访问搜索页面
            url = f"https://creator.xiaohongshu.com/creator/fans"
            page.goto(url)
            print(f"访问页面: {url}")

            # 等待页面加载
            page.wait_for_load_state("networkidle")
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
