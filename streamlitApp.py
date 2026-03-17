import json
import os
import re
import requests
import streamlit as st
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# ---------------------- 1. 基础配置 & 全局常量 ----------------------
load_dotenv()
# 替换为你的智谱API Key
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "请替换为你的智谱API Key")
# 初始化LLM（增加异常捕获）
try:
    llm = ChatZhipuAI(
        api_key=ZHIPU_API_KEY,
        model="glm-4-flash",
        temperature=0,
        timeout=30  # 超时时间
    )
except Exception as e:
    llm = None
    st.warning(f"LLM初始化失败：{str(e)}，仅能使用基础工具功能")

MEMORY_FILE = "agent_memory.json"
# 天气代码映射（更完整）
WEATHER_MAP = {
    0: "晴", 1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "霜", 51: "小雨", 53: "中雨", 55: "大雨",
    61: "小雨", 63: "中雨", 65: "大雨", 71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "强阵雨", 82: "暴雨", 95: "雷暴", 96: "雷暴+冰雹", 99: "雷暴+冰雹"
}

# ---------------------- 2. 工具函数（全异常捕获） ----------------------
def query_weather(city, amap_key="高德key"):
    """真实天气查询（高德地理编码 + Open-Meteo）"""
    if not city:
        return "❌ 天气查询失败：请输入有效城市名（如：北京、上海）"
    
    try:
        # Step1: 高德地图地理编码（国内稳定）
        geo_url = f"https://restapi.amap.com/v3/geocode/geo?address={city}&key={amap_key}"
        geo_res = requests.get(geo_url, timeout=8)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        
        if geo_data.get("status") != "1" or not geo_data.get("geocodes"):
            return f"❌ 天气查询失败：未找到城市「{city}」，请检查拼写或高德Key"
        
        # 解析经纬度
        location = geo_data["geocodes"][0]["formatted_address"]
        lon, lat = geo_data["geocodes"][0]["location"].split(",")
        lat, lon = float(lat), float(lon)
        
        # Step2: Open-Meteo 获取天气数据（不变）
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m&timezone=Asia/Shanghai"
        )
        weather_res = requests.get(weather_url, timeout=8)
        weather_res.raise_for_status()
        data = weather_res.json()
        
        current = data["current_weather"]
        temp = current["temperature"]
        wind = current["windspeed"]
        humidity = data["hourly"]["relative_humidity_2m"][0] if data["hourly"]["relative_humidity_2m"] else "未知"
        weather_code = current["weathercode"]
        weather = WEATHER_MAP.get(weather_code, f"未知({weather_code})")
        
        return f"""
### 📍 {city} 实时天气
- 🌤️ 天气状况：{weather}
- 🌡️ 温度：{temp}℃
- 💨 风速：{wind} km/h
- 💧 湿度：{humidity}%
- 📍 地址：{location}
        """
    except requests.exceptions.Timeout:
        return "❌ 天气查询失败：请求超时，请稍后重试"
    except requests.exceptions.HTTPError as e:
        return f"❌ 天气查询失败：网络错误（{e}）"
    except Exception as e:
        return f"❌ 天气查询失败：{str(e)}"

def calculator(expression):
    """计算器工具 - 高健壮版"""
    if not expression:
        return "❌ 计算失败：请输入有效表达式（如：100+200、3.14*5）"
    
    # 清理表达式（去除空格）
    exp = expression.replace(" ", "")
    # 安全正则匹配（仅允许数字+基础运算符）
    pattern = r"^(\d+\.?\d*)([\+\-\*\/])(\d+\.?\d*)$"
    match = re.match(pattern, exp)
    
    if not match:
        return "❌ 计算失败：表达式格式错误\n✅ 支持格式：数字+运算符+数字（如：100+200、3.14*5）"
    
    num1_str, op, num2_str = match.groups()
    try:
        num1 = float(num1_str)
        num2 = float(num2_str)
        
        if op == "+":
            res = num1 + num2
        elif op == "-":
            res = num1 - num2
        elif op == "*":
            res = num1 * num2
        elif op == "/":
            if num2 == 0:
                return "❌ 计算失败：除数不能为0"
            res = num1 / num2
        else:
            return f"❌ 计算失败：不支持的运算符「{op}」（仅支持 +-*/）"
        
        # 格式化结果（整数去小数位）
        res = int(res) if res.is_integer() else round(res, 2)
        return f"### 🧮 计算结果\n`{exp} = {res}`"
    except Exception as e:
        return f"❌ 计算失败：{str(e)}"

def file_operation(file_path, content=None, mode="read"):
    """文件操作工具 - 高健壮版"""
    if not file_path:
        return "❌ 文件操作失败：请输入有效文件路径（如：calc.txt、D:/test.txt）"
    
    # 规范化路径
    file_path = os.path.normpath(file_path)
    try:
        if mode == "write":
            if content is None:
                return "❌ 文件写入失败：请输入要写入的内容"
            # 确保目录存在
            dir_name = os.path.dirname(file_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"""
### ✅ 文件写入成功
- 📁 文件路径：{os.path.abspath(file_path)}
- 📝 写入内容：{content[:50]}...（仅显示前50字符）
            """
        elif mode == "read":
            if not os.path.exists(file_path):
                return f"❌ 文件读取失败：文件不存在「{os.path.abspath(file_path)}」"
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 统计行数（重置文件指针）
                f.seek(0)
                lines = len(f.readlines())
                words = len(content.replace(" ", "").replace("\n", ""))  # 统计字符数
            
            # 内容过长时截断
            display_content = content if len(content) < 500 else f"{content[:500]}...（内容过长，仅显示前500字符）"
            return f"""
### 📄 文件内容
### 📊 文件统计
- 总行数：{lines} 行
- 字符数：{words} 个
- 文件路径：{os.path.abspath(file_path)}
            """
        else:
            return f"❌ 文件操作失败：不支持的操作模式「{mode}」"
    except PermissionError:
        return f"❌ 文件操作失败：无权限访问「{file_path}」"
    except Exception as e:
        return f"❌ 文件操作失败：{str(e)}"

# ---------------------- 3. 记忆模块（高健壮版） ----------------------
def load_memory():
    """加载对话记忆"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.warning(f"加载记忆失败：{str(e)}，将重置记忆")
        return []

def save_memory(role, content):
    """保存对话记忆"""
    try:
        memory = load_memory()
        memory.append({"role": role, "content": content})
        # 限制记忆长度（避免文件过大）
        if len(memory) > 100:
            memory = memory[-50:]  # 仅保留最后50条
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"保存记忆失败：{str(e)}")

# ---------------------- 4. 核心执行逻辑（全指令容错） ----------------------
def agent_core(user_input):
    """Agent核心处理 - 高健壮版"""
    if not user_input or user_input.strip() == "":
        return "❌ 请输入有效指令（支持：天气查询、计算器、文件读写）"
    
    user_input = user_input.strip().lower()
    save_memory("user", user_input)
    result = ""

    # 1. 天气查询（兼容：北京天气、查北京天气、查询北京天气）
    if any(key in user_input for key in ["天气", "气温", "温度"]):
        city_matches = re.findall(r"(?:查|查询)?\s*([^天气气温温度]+?)\s*(?:天气|气温|温度)", user_input)
        if city_matches:
            city = city_matches[0].strip()
            result = query_weather(city)
        else:
            result = "❌ 天气查询格式错误\n✅ 示例：北京天气、查上海天气、查询广州温度"
    
    # 2. 计算器（兼容：计算100+200、100+200、算3.14*5）
    elif any(key in user_input for key in ["计算", "算", "+-*/"]):
        exp_matches = re.findall(r"(?:计算|算)?\s*([\d\.\+\-\*\/]+)", user_input)
        if exp_matches:
            exp = exp_matches[0].strip()
            result = calculator(exp)
        else:
            result = "❌ 计算格式错误\n✅ 示例：计算100+200、算3.14*5、100/2"
    
    # 3. 文件写入（兼容：写入calc.txt内容300、把300写入calc.txt）
    elif any(key in user_input for key in ["写入", "保存"]):
        # 匹配两种格式：写入[路径]内容[内容]、把[内容]写入[路径]
        pattern1 = r"写入\s*([^\s内容]+?)\s*内容\s*(.+)"
        pattern2 = r"把\s*(.+?)\s*写入\s*([^\s]+)"
        matches1 = re.findall(pattern1, user_input)
        matches2 = re.findall(pattern2, user_input)
        
        if matches1:
            path, content = matches1[0]
            result = file_operation(path.strip(), content.strip(), mode="write")
        elif matches2:
            content, path = matches2[0]
            result = file_operation(path.strip(), content.strip(), mode="write")
        else:
            result = "❌ 文件写入格式错误\n✅ 示例：写入calc.txt内容300、把hello写入test.txt"
    
    # 4. 文件读取（兼容：读取calc.txt、查看calc.txt、读calc.txt）
    elif any(key in user_input for key in ["读取", "查看", "读"]):
        path_matches = re.findall(r"(?:读取|查看|读)\s*([^\s]+)", user_input)
        if path_matches:
            path = path_matches[0].strip()
            result = file_operation(path.strip(), mode="read")
        else:
            result = "❌ 文件读取格式错误\n✅ 示例：读取calc.txt、查看test.txt"
    
    # 5. 普通对话（LLM）
    else:
        if llm is None:
            result = "❌ 普通对话功能不可用：LLM初始化失败，请检查API Key"
        else:
            try:
                memory = load_memory()
                result = llm.invoke(memory).content
            except Exception as e:
                result = f"❌ 对话失败：{str(e)}（请检查API Key是否有效）"
    
    save_memory("assistant", result)
    return result

# ---------------------- 5. Streamlit 界面（交互优化） ----------------------
def main():
    # 页面配置
    st.set_page_config(
        page_title="🤖 AI Agent 智能助手",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 标题 & 说明
    st.title("🤖 AI Agent 智能助手（高健壮版）")
    st.markdown("""
    ### ✅ 支持功能
    - 🌤️ 天气查询：北京天气、查上海气温
    - 🧮 计算器：计算100+200、算3.14*5
    - 📝 文件操作：写入calc.txt内容300、读取calc.txt
    - 💬 普通对话：支持自然语言聊天（需有效智谱API Key）
    """)

    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 显示历史对话
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 输入框
    user_input = st.chat_input(
        placeholder="请输入指令（示例：北京天气、计算100+200、写入calc.txt内容300）",
        key="user_input"
    )

    # 处理用户输入
    if user_input:
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 执行Agent逻辑（加载中）
        with st.spinner("🤔 正在处理..."):
            response = agent_core(user_input)
        
        # 显示Agent回复
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # 保存到会话历史
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # 侧边栏：工具 & 设置
    with st.sidebar:
        st.title("⚙️ 工具面板")
        
        # 清除记忆
        if st.button("🧹 清除对话记忆", type="secondary"):
            if os.path.exists(MEMORY_FILE):
                try:
                    os.remove(MEMORY_FILE)
                    st.session_state.chat_history = []
                    st.success("✅ 对话记忆已清空！")
                except Exception as e:
                    st.error(f"❌ 清除失败：{str(e)}")
            else:
                st.info("ℹ️ 暂无记忆可清除")
        
        # API Key 快速配置
        st.subheader("🔑 API Key 配置")
        api_key_input = st.text_input("智谱API Key", value=ZHIPU_API_KEY, type="password")
        if st.button("💾 保存API Key"):
            if api_key_input and api_key_input != "请替换为你的智谱API Key":
                # 保存到.env文件（如果不存在则创建）
                with open(".env", "w", encoding="utf-8") as f:
                    f.write(f"ZHIPU_API_KEY={api_key_input}")
                st.success("✅ API Key已保存！重启程序生效")
            else:
                st.error("❌ 请输入有效的API Key")
        
        # 版本信息
        st.divider()
        st.caption("📌 版本：v1.0（高健壮版）")
        st.caption("🔧 基于 Streamlit + 智谱GLM")

if __name__ == "__main__":
    main()