def format_text(input_text):
    # 创建替换字典
    emoji_dict = {
        '🧐': '🧐',
        '🎤': '🎤',
        '**': ''  # 移除星号
    }

    # 处理文本
    formatted_text = input_text

    # 移除**符号
    for key, value in emoji_dict.items():
        formatted_text = formatted_text.replace(key, value)

    # 添加合适的段落格式
    paragraphs = formatted_text.split('\n')
    formatted_paragraphs = []

    for p in paragraphs:
        if p.strip():  # 忽略空行
            formatted_paragraphs.append(p)

    return '\n\n'.join(formatted_paragraphs)


# 测试用例
input_text = """** 《理想汽车的AI探索之路：VLA司机大模型的诞生与发展》 **

🚗5月7日，理想汽车推出了理想AI Talk第二季——理想VLA司机大模型🧐。在当晚的活动中，理想汽车董事长兼CEO李想分享了诸多关于人工智能的见解🎤。"""

# 格式化文本
formatted_text = format_text(input_text)

# 打印结果
print(formatted_text)

# 可选：将结果保存到文件
with open('formatted_text.txt', 'w', encoding='utf-8') as f:
    f.write(formatted_text)