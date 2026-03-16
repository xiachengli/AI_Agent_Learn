import json
import os
import requests
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置（整合记忆+工具）
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0.7)
MEMORY_FILE = "full_agent_memory.json"  # 记忆文件路径

# ---------------------- 记忆模块 ----------------------
def load_memory():
    """加载历史记忆（JSON文件）"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ 记忆文件损坏，已重置为空")
            return []
    return []

def save_memory(memory):
    """保存最新记忆到文件"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# ---------------------- 工具模块（适配vvhan天气接口） ----------------------
def query_weather(city):
    """天气查询（优先调用vvhan接口，失败则返回模拟数据）"""
    if not city:
        return "❌ 未指定城市，无法查询天气"
    
    # 1. 尝试调用vvhan天气接口
    try:
        url = f"https://api.vvhan.com/api/weather?city={city}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()  # 抛出HTTP错误
        data = res.json()
        
        # 解析vvhan接口返回结果
        if data.get("success"):
            weather = data["data"]["weather"]
            tem = data["data"]["tem"]
            wind = data["data"]["wind"]
            return f"✅ {city}今日天气：{weather}，温度：{tem}℃，风向：{wind}"
        else:
            raise Exception(f"接口返回失败：{data.get('msg')}")
    
    # 2. 接口调用失败时，返回模拟数据（保证功能可用）
    except Exception as e:
        print(f"⚠️ vvhan天气接口调用失败：{e}，使用模拟数据")
        weather_dict = {
            "北京": "晴", "上海": "多云", "广州": "雷阵雨", 
            "深圳": "晴", "杭州": "阴", "成都": "小雨"
        }
        weather = weather_dict.get(city, "晴")
        tem = "25" if weather == "晴" else "22"
        return f"✅ {city}今日天气：{weather}，温度：{tem}℃，风向：东南风"

def write_file(file_path, content):
    """文件写入工具"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件写入成功：{os.path.abspath(file_path)}"
    except Exception as e:
        return f"❌ 文件写入失败：{str(e)}"

def read_file(file_path):
    """文件读取工具"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{os.path.abspath(file_path)}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"✅ 文件内容：\n{content}"
    except Exception as e:
        return f"❌ 文件读取失败：{str(e)}"

# 工具映射表（核心：工具名称→工具函数）
TOOL_MAP = {
    "天气查询": query_weather,
    "文件写入": write_file,
    "文件读取": read_file
}

# ---------------------- 工具决策函数 ----------------------
def decide_tool(user_input, memory):
    """让LLM解析需求，决定是否调用工具及参数"""
    prompt = f"""
    【角色】AI Agent工具决策器
    【对话历史】{json.dumps(memory, ensure_ascii=False)}
    【用户需求】{user_input}
    【输出要求】严格返回JSON格式，无任何多余内容，字段：
    {{
        "need_tool": true/false,
        "tool_name": "",
        "params": {{}}
    }}
    【工具列表】
    1. 天气查询：参数city（城市名）
    2. 文件写入：参数file_path（文件路径）、content（写入内容）
    3. 文件读取：参数file_path（文件路径）
    """
    # 调用LLM获取决策结果
    response = llm.invoke(prompt)
    clean_res = response.content.strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(clean_res)
    except json.JSONDecodeError:
        return {"need_tool": False, "tool_name": "无", "params": {}}

# ---------------------- 完整Agent核心逻辑 ----------------------
def full_agent(user_input):
    """整合记忆+工具的完整Agent"""
    # 1. 加载历史记忆
    memory = load_memory()
    
    # 2. 工具决策
    decision = decide_tool(user_input, memory)
    
    # 3. 执行工具/直接回答
    if decision["need_tool"] and decision["tool_name"] in TOOL_MAP:
        try:
            # 调用工具
            tool_func = TOOL_MAP[decision["tool_name"]]
            result = tool_func(**decision["params"])
        except Exception as e:
            result = f"❌ 工具调用失败：{str(e)}"
    else:
        # 无需工具，直接调用LLM回答
        memory.append({"role": "user", "content": user_input})
        result = llm.invoke(memory).content
    
    # 4. 保存最新记忆
    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": result})
    save_memory(memory)
    
    return result

# ---------------------- 交互式运行入口 ----------------------
if __name__ == "__main__":
    print("🎯 完整AI Agent（记忆+工具）已启动～")
    print("🔧 支持功能：")
    print("  1. 天气查询（如：北京今日天气）")
    print("  2. 文件写入（如：把'测试内容'写入test.txt）")
    print("  3. 文件读取（如：读取test.txt）")
    print("  4. 普通对话（带持久化记忆）")
    print("💡 输入'退出'结束程序\n")
    
    while True:
        user_input = input("你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        agent_result = full_agent(user_input)
        print(f"Agent：{agent_result}\n")