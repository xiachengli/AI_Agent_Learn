"""
Day9 AI Agent 智能助手（进阶版）
核心功能：
1. 天气查询：实时天气 + 未来6小时预报（高德地理编码 + Open-Meteo）
2. 计算器：支持基础运算，防格式错误/除零异常
3. 文件操作：单文件/批量读写 + 统计
4. 时间查询：实时时间/日期/星期
5. 对话记忆：上下文关联 + 精准清理
6. 高健壮性：全异常捕获 + 友好提示
"""
import json
import os
import re
import requests
import streamlit as st
from datetime import datetime
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# ---------------------- 1. 基础配置 & 全局常量 ----------------------
load_dotenv()

# 敏感配置从.env读取
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
AMAP_KEY = os.getenv("AMAP_KEY", "")

# 初始化LLM
try:
    llm = ChatZhipuAI(
        api_key=ZHIPU_API_KEY,
        model="glm-4-flash",
        temperature=0,
        timeout=30
    )
except Exception as e:
    llm = None
    st.warning(f"LLM初始化失败：{str(e)}，仅能使用基础工具功能")

# 常量定义
MEMORY_FILE = "agent_memory.json"
MAX_MEMORY_LEN = 50  # 最大记忆条数
CITY_ALIAS = {  # 城市别名映射（模糊匹配）
    "京": "北京", "沪": "上海", "粤": "广州", "深": "深圳",
    "杭": "杭州", "苏": "苏州", "宁": "南京", "蓉": "成都"
}
WEATHER_MAP = {  # 天气代码映射
    0: "晴", 1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "霜", 51: "小雨", 53: "中雨", 55: "大雨",
    61: "小雨", 63: "中雨", 65: "大雨", 71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "强阵雨", 82: "暴雨", 95: "雷暴", 96: "雷暴+冰雹", 99: "雷暴+冰雹"
}

# ---------------------- 2. 通用工具函数 ----------------------
def validate_api_key(key, key_type="amap"):
    """验证API Key有效性"""
    if not key or key.strip() == "":
        return False, f"{key_type.upper()} Key未配置"
    
    if key_type == "amap":
        # 高德Key验证
        test_url = f"https://restapi.amap.com/v3/geocode/geo?address=北京&key={key}"
        try:
            res = requests.get(test_url, timeout=5)
            data = res.json()
            if data.get("status") == "1":
                return True, "Key有效"
            else:
                return False, f"Key无效：{data.get('info', '未知错误')}"
        except Exception as e:
            return False, f"验证失败：{str(e)}"
    return True, "Key无需验证"

def format_response(content, title="结果"):
    """统一响应格式"""
    return f"""
### 📌 {title}
{content}
    """

# ---------------------- 3. 核心工具函数 ----------------------
def query_weather(city):
    """
    天气查询（实时+未来6小时预报）
    :param city: 城市名（支持别名，如"京"→"北京"）
    :return: 格式化的天气信息
    """
    # 1. 预处理城市名
    if not city:
        return format_response("请输入有效城市名（如：北京、上海）", "天气查询失败")
    
    city_clean = city.replace("市", "").replace("区", "").replace("县", "")
    city_clean = CITY_ALIAS.get(city_clean, city_clean)  # 别名映射

    # 2. 验证高德Key
    amap_valid, amap_msg = validate_api_key(AMAP_KEY, "amap")
    if not amap_valid:
        return format_response(amap_msg, "天气查询失败")

    try:
        # 3. 高德地理编码获取经纬度
        geo_url = f"https://restapi.amap.com/v3/geocode/geo?address={city_clean}&key={AMAP_KEY}"
        geo_res = requests.get(geo_url, timeout=8)
        geo_res.raise_for_status()
        geo_data = geo_res.json()

        if geo_data.get("status") != "1" or not geo_data.get("geocodes"):
            return format_response(f"未找到城市「{city}」，请检查拼写", "天气查询失败")

        lon, lat = geo_data["geocodes"][0]["location"].split(",")
        lat, lon = float(lat), float(lon)
        location = geo_data["geocodes"][0]["formatted_address"]

        # 4. Open-Meteo获取天气数据（实时+未来6小时）
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current_weather=true&"
            f"hourly=temperature_2m,weathercode,windspeed_10m&"
            f"timezone=Asia/Shanghai&forecast_days=1"
        )
        weather_res = requests.get(weather_url, timeout=8)
        weather_res.raise_for_status()
        data = weather_res.json()

        # 5. 解析实时天气
        current = data["current_weather"]
        current_weather = WEATHER_MAP.get(current["weathercode"], f"未知({current['weathercode']})")
        current_temp = current["temperature"]
        current_wind = current["windspeed"]

        # 6. 解析未来6小时预报
        hourly = data["hourly"]
        forecast_html = ""
        for i in range(6):
            time = hourly["time"][i].split("T")[1]  # 提取小时
            temp = hourly["temperature_2m"][i]
            weather = WEATHER_MAP.get(hourly["weathercode"][i], "未知")
            wind = hourly["windspeed_10m"][i]
            forecast_html += f"- 🕒 {time}：{weather} {temp}℃ 风速{wind}km/h\n"

        # 7. 组装结果
        result = f"""
📍 地址：{location}
🌤️ 实时天气：{current_weather}
🌡️ 实时温度：{current_temp}℃
💨 实时风速：{current_wind} km/h

### 📅 未来6小时预报
{forecast_html}
        """
        return format_response(result, f"{city} 天气信息")

    except requests.exceptions.Timeout:
        return format_response("请求超时，请稍后重试", "天气查询失败")
    except requests.exceptions.HTTPError as e:
        return format_response(f"网络错误：{e}", "天气查询失败")
    except Exception as e:
        return format_response(f"查询失败：{str(e)}", "天气查询失败")

def calculator(expression):
    """
    计算器工具
    :param expression: 运算表达式（如"100+200"）
    :return: 计算结果
    """
    if not expression:
        return format_response("请输入有效表达式（如：100+200、3.14*5）", "计算失败")

    exp = expression.replace(" ", "")
    pattern = r"^(\d+\.?\d*)([\+\-\*\/])(\d+\.?\d*)$"
    match = re.match(pattern, exp)

    if not match:
        return format_response("表达式格式错误\n✅ 支持：数字+运算符+数字（如100+200）", "计算失败")

    try:
        num1 = float(match.group(1))
        op = match.group(2)
        num2 = float(match.group(3))

        if op == "+":
            res = num1 + num2
        elif op == "-":
            res = num1 - num2
        elif op == "*":
            res = num1 * num2
        elif op == "/":
            if num2 == 0:
                return format_response("除数不能为0", "计算失败")
            res = num1 / num2
        else:
            return format_response(f"不支持的运算符「{op}」", "计算失败")

        # 格式化结果
        res = int(res) if res.is_integer() else round(res, 2)
        return format_response(f"`{exp} = {res}`", "计算结果")

    except Exception as e:
        return format_response(f"计算出错：{str(e)}", "计算失败")

def file_operation(file_paths, content=None, mode="read"):
    """
    文件操作（支持单文件/批量）
    :param file_paths: 文件路径列表（如["calc.txt", "test.txt"]）
    :param content: 写入内容（仅mode=write时需要）
    :param mode: 操作模式（read/write）
    :return: 操作结果
    """
    if not file_paths:
        return format_response("请输入有效文件路径（如：calc.txt）", "文件操作失败")

    result = []
    for file_path in file_paths:
        file_path = os.path.normpath(file_path.strip())
        try:
            if mode == "write":
                if content is None:
                    result.append(f"❌ {file_path}：无写入内容")
                    continue

                # 确保目录存在
                dir_name = os.path.dirname(file_path)
                if dir_name and not os.path.exists(dir_name):
                    os.makedirs(dir_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                result.append(f"✅ {file_path}：写入成功\n   内容：{content[:50]}...")

            elif mode == "read":
                if not os.path.exists(file_path):
                    result.append(f"❌ {file_path}：文件不存在")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    f.seek(0)
                    lines = len(f.readlines())
                    words = len(content.replace(" ", "").replace("\n", ""))

                display_content = content if len(content) < 500 else f"{content[:500]}...（超长截断）"
                result.append(f"""
📄 {file_path}
内容：📊 统计：{lines}行 | {words}字符
                """)
            else:
                result.append(f"❌ {file_path}：不支持的模式「{mode}」")

        except PermissionError:
            result.append(f"❌ {file_path}：无访问权限")
        except Exception as e:
            result.append(f"❌ {file_path}：操作失败 - {str(e)}")

    return format_response("\n\n".join(result), f"文件{mode}结果")

def query_time():
    """
    实时时间查询
    :return: 格式化的时间信息
    """
    now = datetime.now()
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[now.weekday()]
    
    result = f"""
🕒 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}
📅 日期：{now.strftime('%Y年%m月%d日')}
🗓️ 星期：{weekday}
⏳ 时间戳：{int(now.timestamp())}
    """
    return format_response(result, "实时时间信息")

# ---------------------- 4. 记忆管理模块 ----------------------
def load_memory():
    """加载对话记忆"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
                # 仅保留最近MAX_MEMORY_LEN条
                return memory[-MAX_MEMORY_LEN:] if len(memory) > MAX_MEMORY_LEN else memory
        return []
    except Exception as e:
        st.warning(f"加载记忆失败：{str(e)}，重置记忆")
        return []

def save_memory(role, content):
    """保存对话记忆"""
    try:
        memory = load_memory()
        memory.append({"role": role, "content": content})
        # 限制长度
        if len(memory) > MAX_MEMORY_LEN:
            memory = memory[-MAX_MEMORY_LEN:]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"保存记忆失败：{str(e)}")

def clear_memory(keyword=None):
    """
    清理记忆（全部/指定关键词）
    :param keyword: 关键词（None则清空全部）
    :return: 清理结果
    """
    try:
        if not os.path.exists(MEMORY_FILE):
            return "✅ 暂无记忆可清理"

        if keyword is None:
            # 清空全部
            os.remove(MEMORY_FILE)
            st.session_state.chat_history = []
            return "✅ 已清空所有对话记忆"
        else:
            # 清理指定关键词
            memory = load_memory()
            new_memory = [msg for msg in memory if keyword not in msg["content"]]
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(new_memory, f, ensure_ascii=False, indent=2)
            # 同步清理会话历史
            st.session_state.chat_history = [
                msg for msg in st.session_state.chat_history if keyword not in msg["content"]
            ]
            return f"✅ 已清理包含「{keyword}」的记忆（剩余{len(new_memory)}条）"
    except Exception as e:
        return f"❌ 清理失败：{str(e)}"

# ---------------------- 5. Agent核心逻辑 ----------------------
def agent_core(user_input):
    """Agent核心处理逻辑"""
    if not user_input or user_input.strip() == "":
        return format_response("请输入有效指令", "输入错误")

    user_input = user_input.strip().lower()
    save_memory("user", user_input)
    result = ""

    # 1. 天气查询
    if any(key in user_input for key in ["天气", "气温", "温度", "预报"]):
        city_matches = re.findall(r"(?:查|查询)?\s*([^天气气温温度预报]+?)\s*(?:天气|气温|温度|预报)", user_input)
        if city_matches:
            result = query_weather(city_matches[0].strip())
        else:
            result = format_response("格式错误\n✅ 示例：北京天气、查上海气温", "天气查询失败")

    # 2. 计算器
    elif any(key in user_input for key in ["计算", "算", "+", "-", "*", "/"]):
        exp_matches = re.findall(r"(?:计算|算)?\s*([\d\.\+\-\*\/]+)", user_input)
        if exp_matches:
            result = calculator(exp_matches[0].strip())
        else:
            result = format_response("格式错误\n✅ 示例：计算100+200、算3.14*5", "计算失败")

    # 3. 文件写入（单文件/批量）
    elif any(key in user_input for key in ["写入", "保存", "批量写入"]):
        # 匹配：批量写入[文件1]和[文件2]内容[内容]
        batch_pattern = r"批量写入\s*([^\s]+?)\s*和\s*([^\s]+?)\s*内容\s*(.+)"
        # 匹配：写入[文件]内容[内容]
        single_pattern = r"写入\s*([^\s内容]+?)\s*内容\s*(.+)"
        
        batch_matches = re.findall(batch_pattern, user_input)
        single_matches = re.findall(single_pattern, user_input)

        if batch_matches:
            file1, file2, content = batch_matches[0]
            result = file_operation([file1, file2], content.strip(), mode="write")
        elif single_matches:
            file_path, content = single_matches[0]
            result = file_operation([file_path], content.strip(), mode="write")
        else:
            result = format_response("格式错误\n✅ 示例：写入calc.txt内容300、批量写入a.txt和b.txt内容hello", "文件写入失败")

    # 4. 文件读取（单文件/批量）
    elif any(key in user_input for key in ["读取", "查看", "批量读取"]):
        # 匹配：批量读取[文件1]和[文件2]
        batch_pattern = r"批量读取\s*([^\s]+?)\s*和\s*([^\s]+)"
        # 匹配：读取[文件]
        single_pattern = r"(?:读取|查看)\s*([^\s]+)"
        
        batch_matches = re.findall(batch_pattern, user_input)
        single_matches = re.findall(single_pattern, user_input)

        if batch_matches:
            file1, file2 = batch_matches[0]
            result = file_operation([file1, file2], mode="read")
        elif single_matches:
            file_path = single_matches[0]
            result = file_operation([file_path], mode="read")
        else:
            result = format_response("格式错误\n✅ 示例：读取calc.txt、批量读取a.txt和b.txt", "文件读取失败")

    # 5. 时间查询
    elif any(key in user_input for key in ["时间", "几点", "星期", "日期"]):
        result = query_time()

    # 6. 普通对话（LLM）
    else:
        if llm is None:
            result = format_response("普通对话不可用：LLM初始化失败（检查智谱API Key）", "对话失败")
        else:
            try:
                memory = load_memory()
                result = llm.invoke(memory).content
                result = format_response(result, "智能回复")
            except Exception as e:
                result = format_response(f"对话失败：{str(e)}", "对话失败")

    save_memory("assistant", result)
    return result

# ---------------------- 6. Streamlit界面 ----------------------
def main():
    # 页面配置
    st.set_page_config(
        page_title="🤖 AI Agent 智能助手（Day9进阶版）",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 标题 & 说明
    st.title("🤖 AI Agent 智能助手（Day9进阶版）")
    st.markdown("""
    ### ✅ 支持功能
    - 🌤️ 天气查询：北京天气、查上海气温（含未来6小时预报）
    - 🧮 计算器：计算100+200、算3.14*5
    - 📝 文件操作：写入calc.txt内容300、批量读取a.txt和b.txt
    - ⏰ 时间查询：现在几点、今天星期几
    - 💬 智能对话：支持上下文关联（需智谱API Key）
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
        placeholder="请输入指令（示例：北京天气、批量写入a.txt和b.txt内容hello、现在几点）",
        key="user_input"
    )

    # 处理用户输入
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("🤔 正在处理..."):
            response = agent_core(user_input)
        
        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # 侧边栏：工具面板
    with st.sidebar:
        st.title("⚙️ 工具面板")

        # 记忆管理
        st.subheader("🧠 记忆管理")
        memory_count = len(load_memory())
        st.caption(f"当前记忆条数：{memory_count}/{MAX_MEMORY_LEN}")
        
        # 清空全部记忆
        if st.button("🗑️ 清空所有记忆", type="secondary"):
            clear_result = clear_memory()
            st.success(clear_result)
        
        # 清理指定记忆
        keyword = st.text_input("输入关键词清理记忆")
        if st.button("🔍 清理指定记忆") and keyword:
            clear_result = clear_memory(keyword)
            st.success(clear_result)

        # API Key配置
        st.subheader("🔑 API配置")
        amap_key_input = st.text_input("高德Web服务Key", value=AMAP_KEY, type="password")
        zhipu_key_input = st.text_input("智谱API Key", value=ZHIPU_API_KEY, type="password")
        
        if st.button("💾 保存API Key"):
            # 写入.env文件
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"AMAP_KEY={amap_key_input}\n")
                f.write(f"ZHIPU_API_KEY={zhipu_key_input}\n")
            st.success("✅ API Key已保存！重启程序生效")

        # 环境检查
        st.subheader("✅ 环境检查")
        if st.button("🔍 检查依赖&Key"):
            # 检查依赖
            try:
                import streamlit, requests, langchain_community, dotenv
                st.success("✅ 所有依赖已安装")
            except ImportError as e:
                st.error(f"❌ 缺失依赖：{e.name}")
            
            # 检查高德Key
            amap_valid, amap_msg = validate_api_key(amap_key_input, "amap")
            st.info(f"高德Key：{amap_msg}")
            
            # 检查智谱Key
            if zhipu_key_input:
                st.info("智谱Key：已配置（需运行时验证）")
            else:
                st.warning("智谱Key：未配置")

        # 版本信息
        st.divider()
        st.caption("📌 Day9进阶版 | Streamlit + 高德 + Open-Meteo")

if __name__ == "__main__":
    main()