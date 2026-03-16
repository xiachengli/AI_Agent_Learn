import json
import os
import requests
import time
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0)

# ---------------------- 增强版工具函数（带重试+参数校验） ----------------------
def query_weather(city, retry_times=2):
    """天气查询：带重试机制（默认重试2次）"""
    # 参数校验
    if not city:
        return "❌ 参数缺失：请指定要查询的城市（如：北京）"
    
    # 重试逻辑
    for i in range(retry_times + 1):
        try:
            url = f"https://api.vvhan.com/api/weather?city={city}"
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            data = res.json()
            if data.get("success"):
                return f"{city}今日天气：{data['data']['weather']}，温度：{data['data']['tem']}℃"
        except Exception as e:
            if i < retry_times:
                print(f"⚠️ 第{i+1}次调用vvhan接口失败：{e}，5秒后重试...")
                time.sleep(5)
                continue
            else:
                # 重试失败，返回模拟数据
                weather_dict = {"北京":"晴","上海":"多云","广州":"雷阵雨"}
                return f"{city}今日天气：{weather_dict.get(city, '晴')}，温度：25℃（模拟数据）"

def write_file(file_path, content, retry_times=1):
    """文件写入：带重试+参数校验"""
    # 参数校验
    if not file_path:
        return "❌ 参数缺失：请指定文件路径（如：weather.txt）"
    if not content:
        return "❌ 参数缺失：请指定写入内容"
    
    # 重试逻辑
    for i in range(retry_times + 1):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ 文件写入成功：{os.path.abspath(file_path)}"
        except Exception as e:
            if i < retry_times:
                print(f"⚠️ 第{i+1}次写入失败：{e}，3秒后重试...")
                time.sleep(3)
                continue
            else:
                return f"❌ 文件写入失败（重试{retry_times}次后仍失败）：{str(e)}"

# 工具映射表 + 参数校验规则
TOOL_MAP = {
    "天气查询": {"func": query_weather, "required_params": ["city"]},
    "文件写入": {"func": write_file, "required_params": ["file_path", "content"]}
}

# ---------------------- 任务规划 + 参数补全 ----------------------
def check_params(tool_name, params):
    """校验工具参数是否完整，返回缺失的参数"""
    if tool_name not in TOOL_MAP:
        return []
    required_params = TOOL_MAP[tool_name]["required_params"]
    missing_params = [p for p in required_params if p not in params or not params[p]]
    return missing_params

def plan_and_execute(user_input):
    """完整流程：拆解任务→参数校验→补全参数→执行任务"""
    # 1. 拆解任务（强化版Prompt，强制LLM输出标准JSON）
    prompt = f"""
【角色】AI Agent任务规划师
【任务】将用户需求拆解为【有序子任务列表】，**只返回纯JSON格式，不要加任何解释、不要代码块、不要换行**：
{{"tasks": [{{"step": 1, "tool_name": "天气查询", "params": {{"city": "北京"}}}}, {{"step": 2, "tool_name": "文件写入", "params": {{"file_path": "bj_weather.txt", "content": "北京今日天气：晴，温度：25℃"}}}}]}}
【工具列表】
- 天气查询：需要参数 city
- 文件写入：需要参数 file_path、content
【用户输入】：{user_input}
【输出要求】
1. 必须是 valid JSON，双引号必须是英文半角；
2. step 从 1 开始递增；
3. tool_name 只能是「天气查询」或「文件写入」；
4. params 里的 key 必须和工具参数完全一致；
5. 不要输出任何其他内容，只返回JSON。
    """
    print(f"🔍 发送给LLM的Prompt：{prompt[:200]}...")  # 调试：打印部分Prompt
    response = llm.invoke(prompt)
    print(f"🔍 LLM原始输出：{response.content}")  # 调试：打印LLM返回内容
    clean_res = response.content.strip()
    # 更彻底的清洗：去掉所有非JSON字符
    clean_res = clean_res.replace("```json", "").replace("```", "").replace("\n", "").replace(" ", "")
    print(f"🔍 清洗后JSON：{clean_res}")  # 调试：打印清洗后内容
    
    try:
        plan_result = json.loads(clean_res)
        tasks = plan_result.get("tasks", [])
    except Exception as e:
        print(f"❌ JSON解析错误：{e}")  # 调试：打印具体错误
        return "❌ 需求拆解失败，请输入更清晰的指令（如：查北京天气并写入bj_weather.txt）"
    
    # 2. 执行任务（带参数补全）
    total_result = "✅ 任务执行结果：\n"
    prev_result = ""
    for task in tasks:
        step = task["step"]
        tool_name = task["tool_name"]
        params = task["params"]
        
        # 3. 参数校验 + 补全
        missing_params = check_params(tool_name, params)
        if missing_params:
            total_result += f"步骤{step}（{tool_name}）：❌ 缺失参数：{','.join(missing_params)}\n"
            return total_result
        
        # 4. 替换上一步结果（多工具协同）
        if prev_result and "content" in params:
            params["content"] = prev_result
        
        # 5. 调用工具
        tool_func = TOOL_MAP[tool_name]["func"]
        result = tool_func(**params)
        prev_result = result
        total_result += f"步骤{step}（{tool_name}）：{result}\n"
    
    return total_result

# ---------------------- 交互式入口 ----------------------
if __name__ == "__main__":
    print("🎯 带错误重试+参数补全的Agent已启动～")
    print("💡 测试指令1（正常）：查北京天气并写入bj_weather.txt")
    print("💡 测试指令2（参数缺失）：查天气并写入文件")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = plan_and_execute(user_input)
        print(f"Agent：\n{result}")