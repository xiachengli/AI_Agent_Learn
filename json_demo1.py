from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json

# 加载API Key（确保.env文件正确）
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 核心函数：自然语言转JSON（修复Markdown代码块问题）
def text_to_json(user_input):
    # 关键Prompt：强化约束，禁止代码块+纯JSON输出
    prompt = f"""
    【角色】结构化数据转换助手
    【任务】将用户的自然语言查询转化为JSON格式，字段固定为：工具名称、城市、日期
    【规则】
    1. 工具名称只能选：机票查询、酒店查询、景点查询；
    2. 日期提取为：今天/明天/后天/具体日期（如2026-03-18）；
    3. 只输出纯JSON字符串，不添加任何解释、备注、换行；
    4. 若信息缺失，对应字段填空字符串；
    5. 绝对不要用```json ```或任何Markdown代码块包裹JSON；
    6. 不要输出任何多余文字，只输出JSON。
    【示例1】
    用户输入：上海飞北京明天的机票？
    输出：{{"工具名称":"机票查询","城市":"上海","日期":"明天"}}
    【示例2】
    用户输入：三亚假日度假酒店价格？
    输出：{{"工具名称":"酒店查询","城市":"三亚","日期":""}}
    【现在请处理】
    用户输入：{user_input}
    """

    # 调用智谱GLM（温度设0，保证输出稳定）
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # 第一步：清洗Markdown代码块（双重保障）
    raw_content = response.choices[0].message.content.strip()
    clean_content = raw_content.replace("```json", "").replace("```", "").strip()

    # 第二步：解析JSON（加异常处理）
    try:
        json_result = json.loads(clean_content)
        return json_result
    except json.JSONDecodeError:
        return {
            "error": "模型输出非JSON格式",
            "原始输出": raw_content,
            "清洗后输出": clean_content
        }

# 测试：杭州后天的机票价格
if __name__ == "__main__":
    test_input = "杭州后天的机票价格"
    result = text_to_json(test_input)
    
    # 格式化输出结果，方便查看
    print("===== 结构化输出结果 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))