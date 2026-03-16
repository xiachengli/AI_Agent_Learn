import json
import os
import requests
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0)

# ---------------------- 1. 定义工具函数 ----------------------
def query_weather(city):
    """真实天气查询（对接免费天气API）"""
    if not city:
        return "❌ 未指定城市，无法查询天气"
    try:
        # 免费天气API（无需申请Key，直接使用）
        url = f"https://api.vvhan.com/api/weather?city={city}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()  # 抛出HTTP错误
        data = res.json()
        if data.get("success") != True:
            return f"❌ 天气查询失败：{data.get('msg', '未知错误')}"
        # 提取关键信息
        weather = data["data"]["weather"]
        tem = data["data"]["tem"]
        wind = data["data"]["wind"]
        return f"✅ {city}今日天气：{weather}，温度：{tem}，风向：{wind}"
    except requests.exceptions.Timeout:
        return "❌ 天气API请求超时"
    except Exception as e:
        return f"❌ 天气查询出错：{str(e)}"

def write_file(file_path, content):
    """文件写入工具"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件已写入：{file_path}"
    except Exception as e:
        return f"❌ 文件写入失败：{str(e)}"

def read_file(file_path):
    """文件读取工具"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"✅ 文件内容：\n{content}"
    except Exception as e:
        return f"❌ 文件读取失败：{str(e)}"

# ---------------------- 2. 工具映射表（核心） ----------------------
TOOL_MAP = {
    "天气查询": query_weather,
    "文件写入": write_file,
    "文件读取": read_file
}

# ---------------------- 3. 工具决策函数 ----------------------
def decide_tool(user_input):
    """让LLM解析用户需求，决策是否调用工具及参数"""
    prompt = f"""
    【角色】工具决策器
    【任务】解析用户需求，返回JSON格式结果，格式必须严格遵守：
    {{
        "need_tool": true/false,  # 是否需要调用工具
        "tool_name": "",          # 工具名称（天气查询/文件写入/文件读取/无）
        "params": {{}}            # 工具参数（如天气查询传city，文件写入传file_path和content）
    }}
    【工具列表】
    1. 天气查询：参数为city（城市名）
    2. 文件写入：参数为file_path（文件路径）、content（写入内容）
    3. 文件读取：参数为file_path（文件路径）
    【示例】
    用户输入：北京今日天气
    输出：{{"need_tool": true, "tool_name": "天气查询", "params": {{"city": "北京"}}}}
    用户输入：把'hello world'写入test.txt
    输出：{{"need_tool": true, "tool_name": "文件写入", "params": {{"file_path": "test.txt", "content": "hello world"}}}}
    用户输入：你好
    输出：{{"need_tool": false, "tool_name": "无", "params": {{}}}}
    【用户输入】
    {user_input}
    """
    # 调用LLM获取决策结果
    response = llm.invoke(prompt)
    # 清洗结果（去除可能的Markdown代码块）
    clean_res = response.content.strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(clean_res)
    except json.JSONDecodeError:
        return {"need_tool": False, "tool_name": "无", "params": {}}

# ---------------------- 4. 核心Agent逻辑 ----------------------
def ai_agent(user_input):
    """整合记忆+工具的完整Agent"""
    # 第一步：工具决策
    decision = decide_tool(user_input)
    if decision["need_tool"] and decision["tool_name"] in TOOL_MAP:
        # 调用工具
        tool_func = TOOL_MAP[decision["tool_name"]]
        tool_result = tool_func(**decision["params"])
        return tool_result
    else:
        # 无需调用工具，直接回答
        return llm.invoke(user_input).content

# ---------------------- 5. 交互式入口 ----------------------
def main():
    print("🎯 带工具扩展的AI Agent已启动（输入'退出'结束）～")
    print("🔧 支持工具：天气查询（如：北京今日天气）、文件写入（如：把'测试内容'写入test.txt）、文件读取（如：读取test.txt）")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = ai_agent(user_input)
        print(f"Agent：{result}")

if __name__ == "__main__":
    main()