from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

# 加载 .env 文件里的密钥
load_dotenv()

# 初始化客户端
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 给 AI 发消息
response = client.chat.completions.create(
    model="glm-4",
    # messages=[
    #     {"role": "user", "content": "你好，请介绍一下AI Agent"}
    # ]
    messages=[
        {"role": "system", "content": "你是一位AI Agent讲师，用大白话给新手讲课，不要用专业术语。"},
        {"role": "user", "content": "帮我写一个Python函数，输入两个数字，返回它们的和。"},
    ]
)

# 输出结果
print(response.choices[0].message.content)