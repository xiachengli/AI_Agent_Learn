# AI Agent 入门学习笔记Day1
## 说明
本笔记为 AI Agent 零基础入门学习路径，从 Prompt 基础到完整 Agent 开发，覆盖核心知识点、代码实战、常见问题，所有代码均基于 Python + 智谱 GLM（免费）实现，可直接复用。

---

## Day1：AI Agent 基础认知
### 核心知识点
1. **AI Agent 定义**：具备自主感知、规划、执行能力的智能系统，区别于普通聊天机器人（能主动调用工具、记忆上下文）。
2. **核心组成**：
   - 大脑（LLM）：如智谱 GLM、通义千问、豆包；
   - 记忆：存储对话/操作历史；
   - 工具调用：对接外部功能（机票查询、代码执行等）；
   - 规划：拆解用户需求，选择执行步骤。
3. **开发环境准备**：
   - 安装 Python 3.8+；
   - 创建虚拟环境：
     ```bash
     # Windows
     python -m venv agent-env
     agent-env\Scripts\activate
     # macOS/Linux
     python3 -m venv agent-env
     source agent-env/bin/activate
     ```
   - 基础依赖：`pip install python-dotenv`。

### 今日任务
- 搭建 Python 虚拟环境；
- 了解主流大模型（智谱 GLM、通义千问、豆包）的免费额度政策；
- 注册智谱 AI 开放平台账号（https://open.bigmodel.cn/）。

---

## Prompt 工程核心
### 核心知识点
1. **Prompt 基本结构**：角色 + 任务 + 规则 + 示例 + 格式约束。
2. **5 类核心 Prompt 模板**：
   | 模板类型       | 适用场景                | 关键要求                     |
   |----------------|-------------------------|------------------------------|
   | 角色设定       | 定向输出（如讲师/助手）| 明确角色定位，约束语言风格   |
   | Few-shot 少样本 | 结构化转换              | 提供 2+ 示例，统一输入输出   |
   | 思维链（CoT）| 复杂任务拆解            | 分步引导，明确逻辑框架       |
   | 工具调用决策   | 工具选择                | 固定输出格式，参数清晰       |
   | 错误修正       | 结果优化                | 指出错误类型，给出修正规则   |
3. **核心原则**：
   - 精准：避免模糊表述；
   - 强约束：明确输出格式/内容限制；
   - 新手友好：避免专业术语，用生活例子。

### 实战代码（Prompt 示例）
```python
# 工具调用决策 Prompt 示例
prompt = """
【角色】AI Agent决策器
【工具列表】
1. 机票查询：输入城市+日期，返回机票价格
2. 酒店查询：输入城市+酒店名，返回价格
3. 景点查询：输入景点名，返回介绍
【任务】判断用户问题需要调用的工具，输出格式：「工具名称-输入参数」
【示例】
用户输入：上海明天的机票？
输出：机票查询-上海-明天
【现在处理】
用户输入：{user_input}
"""
```

### 常见问题
- Prompt 约束不足 → 模型输出偏离预期：增加「只输出XXX，不添加任何解释」强约束；
- 少样本示例不足 → 模型识别规律错误：至少提供 2 个示例。

---

## LLM API 调用实战
### 核心知识点
1. **主流免费 LLM 选择**：
   - 智谱 GLM：https://open.bigmodel.cn/（推荐，免费额度充足）；
   - 豆包：需通过火山引擎方舟平台申请；
   - 通义千问：需付费，新手不推荐。
2. **API 调用核心步骤**：
   - 获取 API Key → 配置环境变量 → 调用 SDK → 解析返回结果。

### 实战代码（智谱 GLM 调用）
```python
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

# 加载环境变量（.env 文件存储 API Key）
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 调用大模型
def call_glm(prompt):
    response = client.chat.completions.create(
        model="glm-4-flash",  # 免费模型
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # 输出稳定
    )
    return response.choices[0].message.content

# 测试
if __name__ == "__main__":
    print(call_glm("什么是AI Agent？用大白话解释"))
```

### 环境配置（.env 文件）
```env
ZHIPU_API_KEY=你的智谱API Key（替换为实际值）
```

### 常见问题
- `ModuleNotFoundError: No module named 'sniffio'` → 安装依赖：`pip install sniffio`；
- `未提供api_key` → 检查 .env 文件名（必须是 .env，而非 zhipu.env）、变量名是否一致。

---

## 结构化输出（JSON）与工具调用
### 核心知识点
1. **结构化输出意义**：纯文本无法被代码解析，JSON 是 Agent 工具调用的「桥梁」。
2. **实现方法**：
   - Prompt 强制约束 JSON 格式，禁止 Markdown 代码块；
   - 代码清洗（去除 ```json ``` 标记）；
   - 异常处理（防止 JSON 解析失败）。
3. **Agent 工具调用闭环**：自然语言 → JSON 解析 → 工具调用 → 返回结果。

### 实战代码（JSON 解析 + 工具调用）
```python
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 模拟工具函数
def query_flight(city, date):
    return f"{date}从{city}出发的机票最低价格：500元"

# 核心函数：自然语言→JSON→工具调用
def agent_tool_call(user_input):
    # 构造 Prompt（强约束 JSON 输出）
    prompt = f"""
    【角色】AI Agent决策器
    【任务】将用户输入转为JSON，字段：工具名称、城市、日期
    【规则】
    1. 工具名称只能是：机票查询/酒店查询/景点查询；
    2. 只输出纯JSON，不用```json ```包裹；
    3. 缺失信息填空字符串。
    【示例】
    用户输入：上海明天机票
    输出：{{"工具名称":"机票查询","城市":"上海","日期":"明天"}}
    用户输入：{user_input}
    """
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # 清洗 + 解析 JSON
    raw_content = response.choices[0].message.content.strip()
    clean_content = raw_content.replace("```json", "").replace("```", "").strip()
    try:
        json_data = json.loads(clean_content)
        tool_name = json_data.get("工具名称")
        city = json_data.get("城市")
        date = json_data.get("日期")
    except json.JSONDecodeError as e:
        return f"解析失败：{e}"

    # 调用工具
    if tool_name == "机票查询":
        result = query_flight(city, date)
    else:
        result = "未知工具"
    return f"执行结果：{result}"

# 测试
if __name__ == "__main__":
    print(agent_tool_call("杭州后天的机票价格"))
```

### 常见问题
- JSON 解析失败 → 模型输出带 ```json ``` 标记：代码中添加清洗逻辑 + Prompt 强化约束；
- 工具调用逻辑错误 → 检查字段名是否匹配（如「工具名称」是否拼写一致）。

---

## Agent 记忆功能（上下文联动）
### 核心知识点
1. **记忆的意义**：从「单次问答」升级为「连续交互」，实现上下文联动。
2. **LangChain 记忆组件**：
   - `ConversationBufferMemory`：存储全部对话历史（简单易上手）；
   - `ConversationSummaryMemory`：总结历史，减少 Prompt 长度（适合长对话）。
3. **实现逻辑**：Memory 组件存储对话历史 → 每次调用 LLM 时传入历史 → 模型基于上下文生成回答。

### 实战代码（带记忆的代码助手）
```python
from langchain.chat_models import ChatZhipuAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from dotenv import load_dotenv
import os

load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 初始化 LLM
llm = ChatZhipuAI(
    api_key=zhipu_api_key,
    model="glm-4-flash",
    temperature=0
)

# 初始化记忆组件
memory = ConversationBufferMemory(return_messages=True)

# 定制 Prompt（代码助手）
code_prompt = """
你是专业的Python代码助手，基于对话历史修改代码，生成可运行、带注释的代码。
当前对话历史：{history}
用户需求：{input}
回答：
"""

# 初始化对话链
conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=ConversationChain.get_default_prompt().from_template(code_prompt),
    verbose=True  # 开启日志，查看历史传递
)

# 交互式对话
def code_chat():
    print("带记忆的代码助手已启动（输入'退出'结束）")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            break
        response = conversation_chain.run(input=user_input)
        print(f"助手：\n{response}")

if __name__ == "__main__":
    code_chat()
```

### 常见问题
- 记忆丢失 → 每次运行代码重置内存，持久化需结合文件/数据库；
- 对话历史过长 → 替换为 `ConversationSummaryMemory`：
  ```python
  from langchain.memory import ConversationSummaryMemory
  memory = ConversationSummaryMemory(llm=llm, return_messages=True)
  ```

---

## 记忆持久化与工具扩展
### 核心知识点
1. **记忆持久化**：将对话历史存储到文件/数据库，避免重启丢失。
2. **工具扩展**：对接真实外部工具（如天气 API、文件操作、网络请求）。
3. **核心库**：
   - `json`：文件存储记忆；
   - `requests`：调用外部 API；
   - `os`：文件操作。

### 实战代码（记忆持久化）
```python
import json
import os
from zhipuai import ZhipuAI
from dotenv import load_dotenv

load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 持久化存储路径
MEMORY_FILE = "agent_memory.json"

# 加载历史记忆
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 保存记忆
def save_memory(memory_list):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_list, f, ensure_ascii=False, indent=2)

# 带持久化记忆的对话
def chat_with_persistent_memory(user_input):
    # 加载历史
    memory = load_memory()
    # 添加新输入
    memory.append({"role": "user", "content": user_input})
    # 调用 LLM
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=memory,
        temperature=0.7
    )
    ai_response = response.choices[0].message.content
    # 保存新回答
    memory.append({"role": "assistant", "content": ai_response})
    save_memory(memory)
    return ai_response

# 测试
if __name__ == "__main__":
    print(chat_with_persistent_memory("写一个读取CSV文件的Python脚本"))
    print(chat_with_persistent_memory("给这个脚本加统计行数功能"))
```

### 实战代码（调用天气 API 工具）
```python
import requests

# 天气查询工具（对接免费API）
def query_weather(city):
    url = f"https://api.vvhan.com/api/weather?city={city}"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        return f"{city}今日天气：{data['data']['weather']}，温度：{data['data']['tem']}"
    except Exception as e:
        return f"天气查询失败：{e}"

# 测试
print(query_weather("北京"))
```

### 常见问题
- 文件读写权限错误 → 检查文件路径是否正确，确保有读写权限；
- API 调用失败 → 检查网络、API 接口是否可用，添加超时处理。

---

## 总结：完整 AI Agent 整合（记忆+工具+规划）
### 核心知识点
1. **完整 Agent 架构**：
   ```mermaid
   graph TD
   A[用户输入] --> B[Prompt 解析]
   B --> C[记忆加载]
   C --> D[工具决策]
   D --> E{是否调用工具}
   E -- 是 --> F[执行工具]
   E -- 否 --> G[直接生成回答]
   F --> H[工具结果整合]
   H --> G
   G --> I[记忆保存]
   I --> J[返回结果给用户]
   ```
2. **核心能力**：需求拆解、工具选择、记忆联动、结果整合。

### 实战代码（完整 Agent）
```python
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
MEMORY_FILE = "agent_memory.json"

# ---------------------- 工具函数 ----------------------
def query_flight(city, date):
    """模拟机票查询"""
    return f"{date}从{city}出发的机票最低价格：500元"

def query_weather(city):
    """真实天气查询"""
    url = f"https://api.vvhan.com/api/weather?city={city}"
    try:
        res = requests.get(url, timeout=5)
        return f"{city}今日天气：{res.json()['data']['weather']}"
    except:
        return "天气查询失败"

def query_scenic(city):
    """模拟景点查询"""
    return f"{city}热门景点：西湖、灵隐寺"

# 工具映射表
TOOL_MAP = {
    "机票查询": query_flight,
    "天气查询": query_weather,
    "景点查询": query_scenic
}

# ---------------------- 记忆功能 ----------------------
def load_memory():
    return json.load(open(MEMORY_FILE, "r", encoding="utf-8")) if os.path.exists(MEMORY_FILE) else []

def save_memory(memory):
    json.dump(memory, open(MEMORY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------------- 核心 Agent 逻辑 ----------------------
def ai_agent(user_input):
    # 1. 加载记忆
    memory = load_memory()
    # 2. 解析用户需求，决策工具
    prompt = f"""
    【角色】AI Agent决策器
    【任务】解析用户需求，返回JSON格式：{{"need_tool": true/false, "tool_name": "", "params": {{}}}}
    【规则】
    1. need_tool：是否需要调用工具（是/否）；
    2. tool_name：可选值：机票查询/天气查询/景点查询/无；
    3. params：工具参数（如机票查询需city、date）；
    4. 只输出纯JSON，无其他内容。
    【示例】
    用户输入：杭州后天的机票价格
    输出：{{"need_tool": true, "tool_name": "机票查询", "params": {{"city": "杭州", "date": "后天"}}}}
    用户输入：你好
    输出：{{"need_tool": false, "tool_name": "无", "params": {{}}}}
    用户输入：{user_input}
    """
    # 调用 LLM 解析需求
    res = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    # 解析决策结果
    clean_content = res.choices[0].message.content.strip().replace("```json", "").replace("```", "")
    try:
        decision = json.loads(clean_content)
    except:
        return "需求解析失败"

    # 3. 执行工具/直接回答
    if decision["need_tool"] and decision["tool_name"] in TOOL_MAP:
        tool_func = TOOL_MAP[decision["tool_name"]]
        # 调用工具（动态传参）
        tool_result = tool_func(**decision["params"])
        answer = f"✅ 工具执行结果：\n{tool_result}"
    else:
        # 直接生成回答（结合记忆）
        memory.append({"role": "user", "content": user_input})
        res = client.chat.completions.create(
            model="glm-4-flash",
            messages=memory,
            temperature=0.7
        )
        answer = res.choices[0].message.content

    # 4. 保存记忆
    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": answer})
    save_memory(memory)
    return answer

# ---------------------- 运行 Agent ----------------------
if __name__ == "__main__":
    print("🎯 完整 AI Agent 已启动，输入'退出'结束")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        print(f"Agent：{ai_agent(user_input)}")
```

### 功能验证
1. 输入：「北京今日天气」→ 调用天气工具，返回真实天气；
2. 输入：「杭州后天的机票价格」→ 调用机票工具，返回模拟结果；
3. 输入：「记住我的名字是小明」→ 记忆保存，后续可查询。

### 常见问题
- 工具参数不匹配 → 检查 `TOOL_MAP` 中函数参数与 JSON 解析的 `params` 是否一致；
- 记忆重复 → 优化记忆加载逻辑，去重重复对话。

---

## 核心总结
### 1. 学习路径
Prompt 基础 → LLM API 调用 → 结构化输出 → 记忆功能 → 记忆持久化 → 工具扩展 → 完整 Agent 整合。
### 2. 关键技术
- Prompt 强约束：确保模型输出符合预期；
- JSON 结构化：实现代码与 LLM 的高效交互；
- 记忆组件：实现上下文联动；
- 工具映射：对接外部功能，扩展 Agent 能力。
### 3. 避坑指南
- 优先使用智谱 GLM（免费、稳定），避免通义千问付费问题；
- 所有 API Key 存储在 .env 文件，避免硬编码；
- 结构化输出必须加清洗+异常处理，防止模型输出格式错误。
### 4. 进阶方向
- 多工具协同调用；
- 复杂需求拆解（多步规划）；
- 记忆总结与压缩；
- Agent 部署（FastAPI/Flask）。