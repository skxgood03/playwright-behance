
import http.client

conn = http.client.HTTPSConnection("us-xpc5-l.xpccdn.com")

payload = ""

headers = {
    'sec-ch-ua-platform': "\"Windows\"",
    'Referer': "https://www.xinpianchang.com/",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    'sec-ch-ua': "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
    'Range': "bytes=0-",
    'sec-ch-ua-mobile': "?0",
    'Accept': "*/*",
    'Accept-Encoding': "gzip, deflate, br",
    'Connection': "keep-alive"
    }
conn.request("GET", "/b9469731-ac0b-4647-b5f9-08721147bb1c/79cb83a9-a334-4eb1-b8a4-16deea0ed56c.mp4", payload, headers)

res = conn.getresponse()
data = res.read()


# 指定保存视频的本地路径
local_video_path = 'D:\\skx\\pachong\\video2.mp4'

# 将数据写入文件
with open(local_video_path, 'wb') as f:
    f.write(data)

print(f"视频已保存到 {local_video_path}")

#
# import re
# text = " https://us-xpc5-l.xpccdn.com/fef167be-5ecf-4290-8b7f-f0e2b9b65fd7/c7d0b235-a090-4891-8fc6-d0e68bd5a953.mp4?j=%7B%22userId%22%3A15485965%2C%22deviceId%22%3A%2234m0keet6ma0hqi6c%22%2C%22ip%22%3A%22223.167.221.19%2C211.95.34.50%22%7D"
#
# pattern2 = r'/[\w-]+/[\w-]+\.mp4'
# result2 = re.search(pattern2, text)
# print(result2.group())