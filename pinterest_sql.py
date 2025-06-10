import requests
import json
import urllib.parse
from tqdm import tqdm
import time
import random


class PinterestScraper:
    def __init__(self, proxy):
        self.base_url = "https://www.pinterest.com/resource/BaseSearchResource/get/"
        self.headers = {
            "accept": "application/json, text/javascript, */*, q=0.01",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.pinterest.com",
            "referer": "https://www.pinterest.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-app-version": "224f552",
            "x-csrftoken": "f0da77587c76532b19b4fee9ae4986b0",
            "x-pinterest-appstate": "active",
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "csrftoken=f0da77587c76532b19b4fee9ae4986b0; _auth=1; _pinterest_sess=TWc9PSYzcmJua0MrTWtka0ZXYm0xWDJ5VXdDZTgvN1JLV1NJREY4Q1dKNi94UFBIT3QrZkcxZTdWbVVJbkRVdlRHSnJzcWE3Ry9yYWVqQkt3QnRnaVZwQkNRS2hvc3I5cXpicUhiZGpycWVBRzREeEM4Vmdpc3JQbVltaFlLdGhCRUFjcXFhVDl1blZKS3ZRY3Znd2VJUGZmV25yMEhZUnpMd2dNcjVCWHpjdjV4dllZUnhPUExMUUE1djNJRGNnajhEQy9TbkQxVk41UVdIK0RvNUNQc3MxMTlySHB1WThZcHVlemNOekswei8xWFdSYTFCT2dIakNkOXhjSTNwOExXK1J1MU96VDhMaE1XMVdtNmg2NXd5ZWVOU0VXVHM2L2hTM2lJclFtcFBQdlJWQUNlNWpmNEZ2OUlKQlhOYkl4WmpkRmtmQmo5K1NFNFFLdmo5bnc1OCtWWnJZQXNCbTh0MXFRWTBOYlhXdjhqMzdISEtFMmNXOG1ZVVU5UzR0TlFocUpUUDk0NUZCelcvOTVvZzlOUEV6UXFnWEtOWFhZM0tLRjduL2pvWTJDZWFMQytML25pVWJkZ1BwK0RUMWh1Y3FrUHZPZ1YwUk95MHpPYWhkRTd6RVpZTGgraGhaQjh2N1h3Z1g0ZEJrei80ZWJ3UFNnQVpkM0lxVWNzeDc3bkZ2MDZEbEdnb2F4a0JkTEFhTzhhLy9Pb2RnU0JtbGc1TWUwb3Nmb2VZY0F6Tnkzc1RVQlFRd3lHcEhUZjZscnRlMnNKR0NoWHVXMVRHUXV3R2hMa2hSQ0Npb1FMZmpSdGc3blVMVTlKR2R0eVJmUEc0ZkdObTB5cS9FcDRrZkZXdUxpSHV5NWxUNll2QjFtREFsTU0wS2R6U09kN2d6aCthb0lZNDFKZzJKaTZ2QjlRR1RWbXk0SjFiWWdVeENWNVlSejNnT0dXbzdWb2FPT20wYnRVZXN2cUxHMFdua25IOFRrYTV4OWFUZjdmY0lCeUpRK0I2eGFJWlowdmZaWGU3UUhDRk95THl5RndrVDFUYWxmR25uWjJYclNuUHV2cU5OVFVaaHlBMTZ5VVI1M2Qva3U5MVBBL1JkOFIyNkhsTGFjOXY0emJQU1RiV1RBWlVsT2I3UVZBRDRzY3IrSVV2T3F6SmF4ZHdaMmFsS0JyUmRGSTA4enFJa1JkSmo1RkQ3Nm5CcWlUNzhQVFBOYUhwL3p1V2wrclFZd1JyVTJFT3M4Y2dkZmVkamJBRExBYVJsMFNuZW1qSWltSWZqZnpTcm5TRUxFWDdtQmZ1QitiNlZiS0NMM1FWR0J4TlQwZ2lxczFBRm91bG0rQjc3R0hjOSs3WXlsMElHTjcyMUtWbytxQUNUR3VPNDRNQkR0VXBxemZ2YjU2VVNTeHFLUjk4R2FWUU9kRUNiQUlHVytNVWpGSDMyZnpLb0IzTyt4VmJDamt4cWg4aEpMclNjUWNXZHdiRkFXTElIUFAxRU5jSU1IUWF1N1pRRTZFTWdTUGg0V0ZLTWxxVzViYS9BS0QzZDJxSlJyUjR6TFJrUy9jTW8yN3NRLytlUnlVSTVkc1NJUUY1cTREeEthaHZocDZzVEpuM1MxaG1kN0cvakU2YWF6UFltRXNXRnhJc09teXlseVdLSDZCajErd2N1cWlEcCs5MS80Mi9rdTgzNGtGZTRWcWVqQk5xUnNqYWhKZS9wdHBLMUFyUFh3Z3lJZjRnSDlSQ1RMTXVXWERmcUNEU2licGxzelBhaHJOTUc1YVlsaXgvc2lkSUR5dEZuYVQ3Y3E=",
        }
        self.proxies = {
            "http": proxy['server'],
            "https": proxy['server']
        }

    def get_search_results(self, query, bookmark=None):
        # 构建请求数据
        source_url = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"

        options = {
            "applied_unified_filters": None,
            "appliedProductFilters": "---",
            "article": None,
            "auto_correction_disabled": False,
            "corpus": None,
            "customized_rerank_type": None,
            "domains": None,
            "filters": None,
            "journey_depth": None,
            "page_size": None,
            "price_max": None,
            "price_min": None,
            "query_pin_sigs": None,
            "query": query,
            "redux_normalize_feed": True,
            "request_params": None,
            "rs": "typed",
            "scope": "pins",
            "selected_one_bar_modules": None,
            "seoDrawerEnabled": False,
            "source_id": None,
            "source_module_id": None,
            "source_url": source_url,
            "top_pin_id": None,
            "top_pin_ids": None,
            "bookmarks": [bookmark] if bookmark else [None]
        }

        data = {
            "source_url": source_url,
            "data": json.dumps({
                "options": options,
                "context": {}
            })
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=data,
                proxies=self.proxies,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if response:
                print(f"Response status code: {response.status_code}")
                print(f"Response text: {response.text[:200]}")
            return None

    def parse_results(self, data, search_query):
        projects = []
        if not data:
            return projects, None

        results = data.get("resource_response", {}).get("data", {}).get("results", [])

        for result in results:
            images = result.get("images", {})
            high_res_url = images.get("orig", {}).get("url", "")

            title = result.get("grid_title", "") or result.get("title", "") or result.get("description", "")

            pinner = result.get("pinner", {})
            author = pinner.get("full_name", "")
            author_url = f"https://www.pinterest.com/{pinner.get('username', '')}"

            likes = result.get("reaction_counts", {}).get("1", 0)

            if high_res_url:
                projects.append({
                    "title": title,
                    "detail_url": high_res_url,
                    "author": author,
                    "author_url": "",
                    "likes": likes,
                    "views": 0,
                    "search": search_query,
                    "platform": "pinterest"
                })

        bookmark = data.get("resource_response", {}).get("bookmark")
        return projects, bookmark

    def search(self, query, total_images=200):
        all_projects = []
        bookmark = None
        pbar = tqdm(total=total_images, desc="Collecting images")
        retry_count = 0
        max_retries = 3
        no_new_data_count = 0
        max_no_new_data = 3  # 连续3次没有新数据就认为已经到达边界

        while len(all_projects) < total_images:
            data = self.get_search_results(query, bookmark)

            if not data:
                retry_count += 1
                print(f"Failed to get data. Retry {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    print("\nMax retries reached. Stopping...")
                    break
                time.sleep(random.uniform(2, 4))
                continue

            retry_count = 0  # 重置重试计数
            projects, new_bookmark = self.parse_results(data, query)

            # 检查是否有新数据
            if not projects:
                no_new_data_count += 1
                print(f"\nNo new data received. Attempt {no_new_data_count}/{max_no_new_data}")
                if no_new_data_count >= max_no_new_data:
                    print("\nReached the end of available data.")
                    break
                time.sleep(random.uniform(1, 2))
                continue

            no_new_data_count = 0  # 重置无数据计数

            # 检查书签是否重复
            if new_bookmark and new_bookmark == bookmark:
                print("\nRepeated bookmark detected. Reached the end of available data.")
                break

            remaining = total_images - len(all_projects)
            projects = projects[:remaining]

            all_projects.extend(projects)
            bookmark = new_bookmark

            # 更新进度条和状态信息
            pbar.update(len(projects))
            print(f"\nCollected {len(all_projects)} images so far")

            time.sleep(random.uniform(1, 2))

        pbar.close()

        # 最终统计信息
        total_collected = len(all_projects)
        if total_collected < total_images:
            print(f"\nWARNING: Only found {total_collected} images out of requested {total_images}")
            print("原因:已到达此搜索查询的可用数据的结尾")
        else:
            print(f"\nSuccessfully collected all {total_images} requested images")

        return all_projects[:total_images]


if __name__ == "__main__":
    # 禁用SSL警告
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 设置代理和搜索参数
    proxy = {
        "server": "http://10.7.100.40:9910"
    }
    search_query = "OMODA C9"
    total_images = 10

    try:
        scraper = PinterestScraper(proxy)
        results = scraper.search(search_query, total_images)

        # 保存结果前检查数据
        if not results:
            print("No results were collected.")
        else:
            uid_list = inster_data(results)
            if len(uid_list) == 0:
                logger.info("没有新作品集需要下载")
                return
            # 使用参数化查询来避免SQL注入
            placeholders = ', '.join(['%s'] * len(uid_list))
            sql = f"""
                    select    `detail_url`,`uid`  from portfolio where uid in ({placeholders}) and is_pick=0

                    """
            cursor.execute(sql, uid_list)  # 执行语句
            data_list = cursor.fetchall()  # 通过fetchall方法获得数据

            # 第二步：抓取项目详情和图片
            # 第二步：抓取项目详情和图片
            scrape_details(data_list, search_query, proxy)

            # 显示详细统计
            print("\nData Statistics:")
            print(f"- 搜索关键词: {search_query}")
            print(f"- 爬取数: {total_images}")
            print(f"- 实际数据: {len(results)}")
            print(f"- 爬取率: {(len(results) / total_images) * 100:.2f}%")

    except Exception as e:
        print(f"An error occurred: {e}")
