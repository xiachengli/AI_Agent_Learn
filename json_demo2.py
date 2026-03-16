from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json

# 加载API Key（确保.env文件正确配置ZHIPU_API_KEY）
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# ---------------------- 模拟工具函数 ----------------------
# 模拟机票查询工具
def query_flight(city, date):
    """模拟机票查询工具，返回固定结果"""
    if not city:
        return "机票查询失败：未指定城市"
    if not date:
        date = "默认日期"
    return f"{date}从{city}出发的机票最低价格：500元"

# 模拟酒店查询工具
def query_hotel(city, date):
    """模拟酒店查询工具，返回固定结果"""
    if not city:
        return "酒店查询失败：未指定城市"
    if not date:
        date = "默认日期"
    return f"{city} {date}的酒店均价：300元/晚"

# 模拟景点查询工具
def query_scenic(city, date):
    """模拟景点查询工具，返回固定结果"""
    if not city:
        return "景点查询失败：未指定城市"
    if not date:
        date = "当日"
    return f"{city}热门景点：西湖、灵隐寺（{date}开放）"

# ---------------------- 核心Agent逻辑 ----------------------
def agent_tool_call(user_input):
    # 第一步：构造Prompt，强制纯JSON输出
    prompt = f"""
    【角色】AI Agent决策器
    【任务】将用户输入转为JSON格式，字段固定为：工具名称、城市、日期
    【严格规则】
    1. 工具名称只能是：机票查询/酒店查询/景点查询；
    2. 日期提取为：今天/明天/后天/具体日期（如2026-03-18），无则填空字符串；
    3. 城市提取用户输入中的核心城市名，无则填空字符串；
    4. 只输出纯JSON字符串，绝对不要用```json ```或任何Markdown代码块包裹；
    5. 不要输出任何解释、备注、换行，仅输出JSON；
    6. 字段值为空时填空字符串（""），不要填null/None。
    【示例1】
    用户输入：上海飞北京明天的机票？
    输出：{{"工具名称":"机票查询","城市":"上海","日期":"明天"}}
    【示例2】
    用户输入：三亚假日度假酒店价格？
    输出：{{"工具名称":"酒店查询","城市":"三亚","日期":""}}
    【示例3】
    用户输入：上海今天的景点介绍
    输出：{{"工具名称":"景点查询","城市":"上海","日期":"今天"}}
    【现在请处理】
    用户输入：{user_input}
    """

    # 调用智谱GLM（温度0保证输出稳定）
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except Exception as e:
        return f"❌ 调用大模型失败：{str(e)}"

    # 第二步：清洗Markdown代码块（双重保障）
    raw_content = response.choices[0].message.content.strip()
    clean_content = raw_content.replace("```json", "").replace("```", "").strip()

    # 第三步：解析JSON（加详细异常处理）
    try:
        json_data = json.loads(clean_content)
        tool_name = json_data.get("工具名称", "")
        city = json_data.get("城市", "")
        date = json_data.get("日期", "")
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败：{str(e)}\n原始输出：{raw_content}\n清洗后：{clean_content}"
    except Exception as e:
        return f"❌ 数据处理失败：{str(e)}"

    # 第四步：根据工具名称调用对应函数
    if tool_name == "机票查询":
        result = query_flight(city, date)
    elif tool_name == "酒店查询":
        result = query_hotel(city, date)
    elif tool_name == "景点查询":
        result = query_scenic(city, date)
    else:
        result = f"❌ 未知工具：{tool_name}（仅支持：机票查询/酒店查询/景点查询）"

    return f"✅ Agent执行结果：\n{result}"

# ---------------------- 测试运行 ----------------------
if __name__ == "__main__":
    # 测试用例1：杭州后天的机票价格
    test_input1 = "杭州后天的机票价格"
    print("===== 测试用例1 =====")
    print(agent_tool_call(test_input1))

    # 测试用例2：上海今天的景点介绍
    test_input2 = "上海今天的景点介绍"
    print("\n===== 测试用例2 =====")
    print(agent_tool_call(test_input2))

    # 测试用例3：三亚明天的酒店价格
    test_input3 = "三亚明天的酒店价格"
    print("\n===== 测试用例3 =====")
    print(agent_tool_call(test_input3))