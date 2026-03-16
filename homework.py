import json
import os
import re
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置（彻底移除vvhan接口依赖）
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0)

# ---------------------- 工具模块（无任何外部API依赖） ----------------------
# 1. 天气查询（纯模拟，无vvhan接口）
def query_weather(city):
    """纯模拟天气查询（无任何外部接口调用）"""
    if not city:
        return "❌ 参数缺失：请指定城市（如北京）"
    weather_dict = {
        "北京": "晴", "上海": "多云", "广州": "雷阵雨", 
        "深圳": "晴", "杭州": "阴", "成都": "小雨"
    }
    weather = weather_dict.get(city, "晴")
    tem = "25" if weather == "晴" else "22"
    return f"{city}今日天气：{weather}，温度：{tem}℃"

# 2. 文件写入
def write_file(file_path, content):
    """文件写入工具"""
    if not file_path or not content:
        return "❌ 参数缺失：file_path（文件路径）和content（内容）必须都有"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件写入成功：{os.path.abspath(file_path)}"
    except Exception as e:
        return f"❌ 文件写入失败：{str(e)}"

# 3. 文件读取
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

# 4. 新增：计算器工具（支持加减乘除）
def calculator(expression):
    """计算器工具：支持 数字+运算符+数字 格式（如100+200、50*8）"""
    if not expression:
        return "❌ 参数缺失：请输入计算表达式（如100+200）"
    
    # 提取数字和运算符（简单正则匹配）
    pattern = r"(\d+)([\+\-\*\/])(\d+)"
    match = re.match(pattern, expression.strip())
    if not match:
        return f"❌ 表达式格式错误：仅支持 数字+运算符+数字（如100+200），当前输入：{expression}"
    
    num1 = float(match.group(1))
    op = match.group(2)
    num2 = float(match.group(3))
    
    # 计算逻辑
    try:
        if op == "+":
            result = num1 + num2
        elif op == "-":
            result = num1 - num2
        elif op == "*":
            result = num1 * num2
        elif op == "/":
            if num2 == 0:
                return "❌ 除数不能为0"
            result = num1 / num2
        else:
            return f"❌ 不支持的运算符：{op}（仅支持+、-、*、/）"
        return f"{expression} = {result}"
    except Exception as e:
        return f"❌ 计算失败：{str(e)}"

# 5. 新增：统计文件行数工具
def count_file_lines(file_path):
    """统计文件行数工具"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{os.path.abspath(file_path)}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = len(f.readlines())  # 统计总行数
        return f"✅ {file_path} 总行数：{lines} 行"
    except Exception as e:
        return f"❌ 统计行数失败：{str(e)}"

# 工具映射表（新增计算器、统计行数）
TOOL_MAP = {
    "天气查询": {"func": query_weather, "required_params": ["city"]},
    "文件写入": {"func": write_file, "required_params": ["file_path", "content"]},
    "文件读取": {"func": read_file, "required_params": ["file_path"]},
    "计算器": {"func": calculator, "required_params": ["expression"]},
    "统计文件行数": {"func": count_file_lines, "required_params": ["file_path"]}
}

# ---------------------- 任务规划模块（优化后支持新工具） ----------------------
def plan_task(user_input):
    """强化版任务规划：支持计算器、统计行数"""
    prompt = f"""
【角色】AI Agent任务规划师
【任务】将用户需求拆解为有序子任务列表，**只返回纯JSON，无任何多余内容**：
{{
    "tasks": [
        {{"step": 1, "tool_name": "工具名", "params": {{"参数名": "参数值"}}}},
        {{"step": 2, "tool_name": "工具名", "params": {{"参数名": "参数值"}}}}
    ]
}}
【工具列表及参数】
1. 天气查询：参数city（城市名）
2. 文件写入：参数file_path（文件路径）、content（写入内容）
3. 文件读取：参数file_path（文件路径）
4. 计算器：参数expression（计算表达式，如100+200）
5. 统计文件行数：参数file_path（文件路径）
【示例1】用户输入：计算100+200并写入calc.txt
输出：{{"tasks": [{{"step":1,"tool_name":"计算器","params":{{"expression":"100+200"}}}},{{"step":2,"tool_name":"文件写入","params":{{"file_path":"calc.txt","content":"100+200 = 300.0"}}}}]}}
【示例2】用户输入：读取weather.txt并统计行数
输出：{{"tasks": [{{"step":1,"tool_name":"文件读取","params":{{"file_path":"weather.txt"}}}},{{"step":2,"tool_name":"统计文件行数","params":{{"file_path":"weather.txt"}}}}]}}
【用户输入】{user_input}
【强制要求】
1. 仅返回JSON，不要代码块、不要解释、不要换行
2. step从1开始递增
3. tool_name必须是工具列表里的名称
"""
    # 调用LLM并清洗结果
    response = llm.invoke(prompt)
    clean_res = response.content.strip().replace("```json", "").replace("```", "").replace("\n", "").replace(" ", "")
    try:
        return json.loads(clean_res)
    except:
        return {"tasks": []}

# ---------------------- 执行规划任务 ----------------------
def execute_planned_tasks(user_input):
    """执行拆解后的任务（支持新工具协同）"""
    # 1. 拆解任务
    plan_result = plan_task(user_input)
    tasks = plan_result.get("tasks", [])
    if not tasks:
        return "❌ 无法拆解需求，请输入示例格式（如：计算100+200并写入calc.txt）"
    
    # 2. 按序执行
    total_result = "✅ 任务执行结果：\n"
    prev_result = ""
    for task in tasks:
        step = task["step"]
        tool_name = task["tool_name"]
        params = task["params"]
        
        # 参数校验
        if tool_name not in TOOL_MAP:
            total_result += f"步骤{step}：❌ 未知工具：{tool_name}\n"
            continue
        missing_params = [p for p in TOOL_MAP[tool_name]["required_params"] if p not in params or not params[p]]
        if missing_params:
            total_result += f"步骤{step}（{tool_name}）：❌ 缺失参数：{','.join(missing_params)}\n"
            continue
        
        # 多工具协同：用上一步结果填充content
        if prev_result and "content" in params:
            params["content"] = prev_result
        
        # 调用工具
        tool_func = TOOL_MAP[tool_name]["func"]
        result = tool_func(**params)
        prev_result = result
        total_result += f"步骤{step}（{tool_name}）：{result}\n"
    
    return total_result

# ---------------------- 交互式入口 ----------------------
if __name__ == "__main__":
    print("🎯 AI Agent（计算器+统计行数）已启动～")
    print("💡 支持的复杂任务：")
    print("  1. 计算100+200并写入calc.txt")
    print("  2. 读取weather.txt并统计行数")
    print("  3. 查北京天气并写入weather.txt，再统计行数")
    print("💡 输入'退出'结束\n")
    
    while True:
        user_input = input("你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = execute_planned_tasks(user_input)
        print(f"Agent：\n{result}")
