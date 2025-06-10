import requests
import math
import json
import time
from typing import List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class XinPianChangCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-nextjs-data": "1"
        }
        self.cookies = {
            "FECW": "e74e982eb32f02e54f033776d13b339552dccdec343bb94ccf77096feeab69543519d83c37975a34b7d304bfb9a426ef6c4c2153cff20a7f5a89ef777448adb0f049f4c2523865e6a2ee4c2144b84f07c6",
            "Device_ID": "34m0keet6ma0hqi6c",
            "Authorization": "6268231C6E27143FB6E27140C16E2719F096E271AC4C70719AE5"
        }

    def get_kw_id(self, keyword: str) -> int:
        """获取关键词对应的ID"""
        url = f"https://www.xinpianchang.com/api/xpc/v2/search/getSearchKwIdByKw?kw={keyword}"

        try:
            response = self.session.get(url, headers=self.headers, cookies=self.cookies)
            response.raise_for_status()
            data = response.json()
            print(data)
            if data["status"] == 0 and "data" in data:
                return data["data"]["id"]
            else:
                logging.error(f"获取kw_id失败: {data}")
                return None

        except Exception as e:
            logging.error(f"请求kw_id出错: {str(e)}")
            return None

    def get_media_list(self, kw_id: int, page: int = 1) -> List[str]:
        """获取视频列表"""
        url = f"https://www.xinpianchang.com/_next/data/No3os6GFzLUZG_K5Z_L4_/search.json"
        params = {
            "page": page,
            "kw_id": kw_id,
            "FECU": "3oovg0uhwMbfa/n/7boZi4jJqIOEec//YC3v85+RowEdLfSaaO6VQVlGjURNgM5j7uMCS/XBmPzWXunxVCyCwNKrX5WqpZw3yIrHMJlX6dE+I21L59QHAp64yh8gy1Fu4LrUpSUCT/30PVw0cRTau68FNXCtgASpJeF5TkWbPoKfHHHR+3JIuKvXkCEC/wNvm1",
        }

        try:
            response = self.session.get(url, params=params, headers=self.headers, cookies=self.cookies)
            response.raise_for_status()
            data = response.json()




            if "pageProps" in data and "searchData" in data["pageProps"]:
                video_list = data["pageProps"]["searchData"]["list"]
                per_page = data["pageProps"]["searchData"]["perPage"]

                media_ids = [{item["media_id"] if "media_id" in item else "None": item["id"] if "id" in item else "None"} for item in video_list]
                return media_ids, per_page
            else:
                logging.error(f"获取视频列表失败: {data}")
                return [], 0

        except Exception as e:
            logging.error(f"请求视频列表出错: {str(e)}")
            return [], 0

    def crawl_videos(self, keyword: str, total_videos: int) -> List[str]:
        """爬取指定数量的视频ID"""
        kw_id = self.get_kw_id(keyword)
        if not kw_id:
            return []

        all_media_ids = []
        current_page = 1

        first_page_ids, per_page = self.get_media_list(kw_id)
        all_media_ids.extend(first_page_ids)

        if per_page == 0:
            return []

        total_pages = math.ceil(total_videos / per_page)

        # 爬取剩余页面
        for page in range(2, total_pages + 1):
            logging.info(f"正在爬取第 {page} 页")
            media_ids, _ = self.get_media_list(kw_id, page)
            if media_ids==[]:
                logging.warning(f"第 {page} 页没有获取到任何视频ID,结束")
                break
            all_media_ids.extend(media_ids)

            if len(all_media_ids) >= total_videos:
                break

            time.sleep(1)  # 添加延时避免请求过快

        return all_media_ids[:total_videos]


def main():
    crawler = XinPianChangCrawler()

    # 使用示例
    keyword = input("请输入搜索关键词: ")
    try:
        total_videos = int(input("请输入需要爬取的视频数量: "))
    except ValueError:
        logging.error("请输入有效的数字")
        return

    logging.info(f"开始爬取关键词 '{keyword}' 的视频")
    media_ids = crawler.crawl_videos(keyword, total_videos)

    if media_ids:
        logging.info(f"成功爬取 {len(media_ids)} 个视频ID")

        # 将结果保存到文件
        with open(f"{keyword}_media_ids.json", "w", encoding="utf-8") as f:
            json.dump(media_ids, f, ensure_ascii=False, indent=2)
        logging.info(f"结果已保存到 {keyword}_media_ids.json")
    else:
        logging.error("未获取到任何视频ID")


if __name__ == "__main__":
    main()