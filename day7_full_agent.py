import json
import os
import requests
import time
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置（整合记忆+任务规划+多工具协同+错误重试）
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0.7)
MEMORY_FILE = "day7_agent_memory.json"  # 记忆持久化文件

# ---------------------- 1. 记忆模块（复用Day6） ----------------------
def load_memory():
    """加载历史记忆"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(memory, user_input, result):
    """保存最新对话到记忆"""
    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": result})
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# ---------------------- 2. 工具模块（适配vvhan+重试+参数校验） ----------------------
def query_weather(city, retry_times=2):
    """天气查询：vvhan接口+重试+降级模拟"""
    if not city:
        return "❌ 参数缺失：city（城市名）"
    for i in range(retry_times + 1):
        try:
            url = f"https://api.vvhan.com/api/weather?city={city}"
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            data = res.json()
            if data.get("success"):
                return f"{city}今日天气：{data['data']['weather']}，温度：{data['data']['tem']}℃"
        except:
            if i < retry_times:
                time.sleep(3)
                continue
            else:
                return f"{city}今日天气：晴，温度：25℃（模拟数据）"

def write_file(file_path, content, retry_times=1):
    """文件写入：重试+参数校验"""
    if not file_path:
        return "❌ 参数缺失：file_path（文件路径）"
    if not content:
        return "❌ 参数缺失：content（写入内容）"
    for i in range(retry_times + 1):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ 文件写入成功：{file_path}"
        except:
            if i < retry_times:
                time.sleep(2)
                continue
            else:
                return f"❌ 文件写入失败：{str(e)}"

def read_file(file_path):
    """文件读取：参数校验"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f"✅ 文件内容：\n{f.read()}"
    except Exception as e:
        return f"❌ 文件读取失败：{str(e)}"

# 工具映射表（含参数校验规则）
TOOL_MAP = {
    "天气查询": {"func": query_weather, "required": ["city"]},
    "文件写入": {"func": write_file, "required": ["file_path", "content"]},
    "文件读取": {"func": read_file, "required": ["file_path"]}
}

# ---------------------- 3. 任务规划模块 ----------------------
def plan_task(user_input, memory):
    """结合记忆拆解复杂任务"""
    prompt = f"""
    基于对话历史：{json.dumps(memory, ensure_ascii=False)}
    拆解用户需求为有序子任务，返回JSON：{{"tasks": [{{"step":1,"tool_name":"","params":{{}}}}]}}
    工具列表：天气查询（city）、文件写入（file_path,content）、文件读取（file_path）
    用户需求：{user_input}
    """
    response = llm.invoke(prompt)
    clean_res = response.content.strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(clean_res)
    except:
        return {"tasks": []}

# ---------------------- 4. 核心执行模块 ----------------------
def execute_task(task):
    """执行单个子任务（参数校验+工具调用）"""
    tool_name = task["tool_name"]
    params = task["params"]
    if tool_name not in TOOL_MAP:
        return f"❌ 未知工具：{tool_name}"
    
    # 参数校验
    missing = [p for p in TOOL_MAP[tool_name]["required"] if p not in params or not params[p]]
    if missing:
        return f"❌ 缺失参数：{','.join(missing)}"
    
    # 调用工具
    tool_func = TOOL_MAP[tool_name]["func"]
    return tool_func(**params)

def full_agent(user_input):
    """完整Agent：记忆+任务规划+多工具协同+错误重试"""
    # 1. 加载记忆
    memory = load_memory()
    
    # 2. 任务规划
    plan_result = plan_task(user_input, memory)
    tasks = plan_result.get("tasks", [])
    if not tasks:
        # 无规划任务，直接回答
        result = llm.invoke(memory + [{"role": "user", "content": user_input}]).content
        save_memory(memory, user_input, result)
        return result
    
    # 3. 按序执行子任务
    total_result = "✅ 复杂任务执行结果：\n"
    prev_result = ""
    for task in tasks:
        step = task["step"]
        # 替换上一步结果（协同）
        if prev_result and "content" in task["params"]:
            task["params"]["content"] = prev_result
        # 执行任务
        step_result = execute_task(task)
        prev_result = step_result
        total_result += f"步骤{step}：{step_result}\n"
    
    # 4. 保存记忆
    save_memory(memory, user_input, total_result)
    return total_result

# ---------------------- 5. 交互式入口 ----------------------
if __name__ == "__main__":
    print("🎯 Day7 完整AI Agent（记忆+任务规划+多工具协同）已启动～")
    print("🔧 支持功能：")
    print("  1. 复杂任务：查广州天气并写入gz_weather.txt，再读取该文件")
    print("  2. 普通对话：带持久化记忆")
    print("  3. 错误重试：vvhan接口失败自动降级模拟数据")
    print("💡 输入'退出'结束程序\n")
    
    while True:
        user_input = input("你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = full_agent(user_input)
        print(f"Agent：\n{result}\n")