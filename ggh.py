import requests

WECHAT_APPID = "wxe170ccb6946ac7ed"  # 微信公众号 AppID
WECHAT_APPSECRET = "1abb242f6404e028ad7420f0e8513a51"  # 微信公众号 AppSecret
WECHAT_API_URL = "https://api.weixin.qq.com"


# 获取微信公众号的 access_token
def get_wechat_access_token():
    url = f"{WECHAT_API_URL}/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_APPSECRET}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            if 'access_token' in result:
                return result['access_token']
            else:
                print(f"获取 access_token 失败，错误信息：{result}")
    except requests.RequestException as e:
        print(f"获取 access_token 发生错误：{e}")
    return None


# 上传封面图片并获取 media_id
def upload_cover_image(access_token, image_path):
    url = f"{WECHAT_API_URL}/cgi-bin/media/upload?access_token={access_token}&type=image"
    with open(image_path, 'rb') as file:
        files = {'media': file}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                result = response.json()
                if 'media_id' in result:
                    return result['media_id']
                else:
                    print(f"上传封面图片失败，错误信息：{result}")
            else:
                print(f"上传封面图片请求失败，状态码：{response.status_code}，错误信息：{response.text}")
        except requests.RequestException as e:
            print(f"上传封面图片发生错误：{e}")
    return None


# 创建文章素材
def create_article_material(access_token, article, thumb_media_id):
    url = f"{WECHAT_API_URL}/cgi-bin/media/uploadnews?access_token={access_token}"
    data = {
        "articles": [
            {
                "title": "强制下班热点文章",  # 文章标题
                "thumb_media_id": thumb_media_id,  # 封面图片素材 ID
                "author": "Your Name",  # 作者
                "digest": "文章摘要",  # 文章摘要
                "show_cover_pic": 0,  # 是否显示封面图片
                "content": article,
                "content_source_url": ""  # 原文链接
            }
        ]
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'media_id' in result:
                return result['media_id']
            else:
                print(f"创建文章素材失败，错误信息：{result}")
    except requests.RequestException as e:
        print(f"创建文章素材发生错误：{e}")
    return None


# 发布文章
def publish_article(access_token, media_id):
    url = f"{WECHAT_API_URL}/cgi-bin/message/mass/sendall?access_token={access_token}"
    data = {
        "filter": {
            "is_to_all": True  # 注意这里改为 Python 布尔值 True
        },
        "mpnews": {
            "media_id": media_id
        },
        "msgtype": "mpnews"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print("文章发布成功")
            else:
                print(f"文章发布失败，错误信息：{result}")
    except requests.RequestException as e:
        print(f"文章发布发生错误：{e}")

if  __name__ == '__main__':
    token = get_wechat_access_token()
    print(token)
    image = upload_cover_image(token, "8b52b4870182f2883e8f94b231680fd6.jpg")
    print(image)
    iss = create_article_material(token, "测试", image)
    print(iss)
    over = publish_article(token, iss)



    print(over)
