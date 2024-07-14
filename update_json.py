import sys
import os
import json

# 获取传递的已处理微博链接列表的 JSON 字符串
processed_weibos_str = os.getenv("processed_weibos")

# 将 JSON 字符串解析为列表
processed_weibos = json.loads(processed_weibos_str)

# 定义要更新的 JSON 文件路径
weibo_data_file = 'json_data/weibo_data.json'  # 替换为你的 JSON 文件路径

# 将已处理的微博链接列表保存到 JSON 文件中
with open(weibo_data_file, 'w') as f:
    json.dump(processed_weibos, f)
