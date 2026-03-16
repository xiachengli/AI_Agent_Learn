import json
import os
import requests
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0)

# ---------------------- 工具函数（适配 vvhan 天气接口） ----------------------
def query_weather(city):
    """天气查询：优先调用vvhan接口，失败降级模拟数据"""
    if not city:
        return "❌ 未指定城市，无法查询天气"
    try:
        # 调用vvhan天气接口
        url = f"https://api.vvhan.com/api/weather?city={city}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        if data.get("success"):
            weather = data["data"]["weather"]
            tem = data["data"]["tem"]
            wind = data["data"]["wind"]
            return f"{city}今日天气：{weather}，温度：{tem}℃，风向：{wind}"
        else:
            raise Exception(data.get("msg", "接口返回失败"))
    except Exception as e:
        print(f"⚠️ vvhan接口调用失败：{e}，使用模拟数据")
        # 模拟天气数据
        weather_dict = {"北京":"晴","上海":"多云","广州":"雷阵雨","深圳":"晴"}
        return f"{city}今日天气：{weather_dict.get(city, '晴')}，温度：25℃，风向：东南风"

def write_file(file_path, content):
    """文件写入工具"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件写入成功：{file_path}"
    except Exception as e:
        return f"文件写入失败：{str(e)}"

# 工具映射表
TOOL_MAP = {"天气查询": query_weather, "文件写入": write_file}

# ---------------------- 核心：任务规划函数 ----------------------
def plan_task(user_input):
    """让LLM拆解复杂需求为有序子任务（JSON格式）"""
    prompt = f"""
    【角色】AI Agent任务规划师
    【任务】将用户的复杂需求拆解为有序子任务列表，严格返回JSON格式，无任何多余内容：
    {{
        "tasks": [
            {{
                "step": 1,          // 步骤编号（从1开始）
                "tool_name": "",    // 工具名称（天气查询/文件写入）
                "params": {{}}      // 工具参数（如天气查询传city，文件写入传file_path+content）
            }}
        ]
    }}
    【示例】
    用户输入：查北京天气并写入weather.txt
    输出：{{"tasks": [{{"step":1,"tool_name":"天气查询","params":{{"city":"北京"}}}},{{"step":2,"tool_name":"文件写入","params":{{"file_path":"weather.txt","content":"北京今日天气：晴，温度：25℃，风向：东南风"}}}}]}}
    【注意】
    1. 子任务必须按执行顺序排列；
    2. 文件写入的content要基于前一步的天气查询结果（用模拟值占位即可）；
    3. 只返回JSON，不添加任何解释、代码块。
    【用户需求】
    {user_input}
    """
    # 调用LLM获取拆解结果
    response = llm.invoke(prompt)
    clean_res = response.content.strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(clean_res)
    except json.JSONDecodeError:
        return {"tasks": []}

# ---------------------- 执行规划任务 ----------------------
def execute_planned_tasks(user_input):
    """拆解任务→按序执行→返回总结果"""
    # 1. 拆解任务
    plan_result = plan_task(user_input)
    tasks = plan_result.get("tasks", [])
    if not tasks:
        return "❌ 无法拆解需求，请输入更清晰的指令（如：查北京天气并写入weather.txt）"
    
    # 2. 按序执行子任务
    total_result = "✅ 任务执行结果：\n"
    prev_result = ""  # 存储上一步结果，用于多工具协同
    for task in tasks:
        step = task["step"]
        tool_name = task["tool_name"]
        params = task["params"]
        
        # 替换参数中的占位符（用上一步结果）
        if prev_result and "content" in params:
            params["content"] = prev_result
        
        # 调用工具
        if tool_name in TOOL_MAP:
            result = TOOL_MAP[tool_name](**params)
            prev_result = result  # 保存当前结果给下一步用
            total_result += f"步骤{step}（{tool_name}）：{result}\n"
        else:
            total_result += f"步骤{step}（{tool_name}）：❌ 未知工具\n"
    
    return total_result

# ---------------------- 交互式入口 ----------------------
if __name__ == "__main__":
    print("🎯 带任务规划的AI Agent已启动（输入'退出'结束）～")
    print("💡 示例指令：查上海天气并写入sh_weather.txt")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = execute_planned_tasks(user_input)
        print(f"Agent：\n{result}")