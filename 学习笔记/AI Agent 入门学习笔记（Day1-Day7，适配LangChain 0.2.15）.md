# AI Agent 入门学习笔记（Day1-Day7，适配LangChain 0.2.15）

说明：本笔记为AI Agent零基础入门学习路径，基于 **Python 3.8+** + **智谱GLM-4-Flash（免费）** + **LangChain 0.2.15** 实现，所有代码均已修正导入路径、解决版本兼容问题，可直接复制运行，覆盖核心知识点、代码实战、常见问题与避坑指南。

# Day1：AI Agent 基础认知与环境搭建

## 一、核心知识点

- **AI Agent 定义**：具备自主感知、规划、执行能力的智能系统，区别于普通聊天机器人——能主动调用工具、记忆上下文，实现“理解需求→执行任务→反馈结果”的闭环。

- **核心组成（四大模块）**：
        

    - 大脑（LLM）：核心决策单元，如智谱GLM、豆包（本笔记统一用智谱GLM-4-Flash，免费且稳定）；

    - 记忆：存储对话历史、操作记录，实现上下文联动；

    - 工具调用：对接外部功能（天气查询、文件操作、API调用等）；

    - 规划：拆解复杂用户需求，选择最优执行步骤。

- **开发环境准备**：优先搭建Python虚拟环境，避免依赖冲突。

## 二、实战操作（环境搭建）

### 1. 安装Python

安装Python 3.8+（推荐3.10），勾选“Add Python to PATH”，安装完成后验证：

```bash
python --version  # Windows
python3 --version # macOS/Linux
```

### 2. 创建并激活虚拟环境

```bash
# 1. 创建虚拟环境（环境名：agent-env，可自定义）
# Windows
python -m venv agent-env
# 激活虚拟环境
agent-env\Scripts\activate

# macOS/Linux
python3 -m venv agent-env
# 激活虚拟环境
source agent-env/bin/activate
```

激活成功后，终端会显示 `(agent-env)`，后续所有操作均在该环境中执行。

### 3. 安装基础依赖

```bash
pip install python-dotenv  # 加载环境变量（存储API Key）
```

## 三、今日任务（必做）

1. 搭建上述Python虚拟环境，确保激活成功；

2. 注册智谱AI开放平台账号（[https://open.bigmodel.cn/](https://open.bigmodel.cn/)），获取API Key（个人中心→API密钥）；

3. 了解智谱GLM-4-Flash的免费额度（足够新手学习使用）。

## 四、常见问题

- Windows激活虚拟环境报错“权限不足”：以管理员身份运行终端，重新执行激活命令；

- pip安装速度慢：更换国内源（临时使用）：`pip install python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple/`。

# Day2：Prompt 工程核心（Agent的“指令大脑”）

## 一、核心知识点

- **Prompt 定义**：给LLM的“指令”，决定LLM的输出方向和格式，是AI Agent的核心基础——好的Prompt能让Agent精准执行任务。

- **Prompt 基本结构**（必含5要素）：
        

    1. 角色：明确LLM的身份（如“AI Agent决策器”“Python代码助手”）；

    2. 任务：明确要完成的事情（如“解析需求、调用工具”“生成可运行代码”）；

    3. 规则：约束输出格式、内容范围（如“只输出JSON”“代码带注释”）；

    4. 示例（可选，推荐）：复杂任务提供1-2个示例，降低LLM理解成本；

    5. 格式约束：明确输出格式（如JSON、代码块、纯文本）。

- **5类核心Prompt模板（Agent常用）**：

|模板类型|适用场景|关键要求|
|---|---|---|
|角色设定|定向输出（如代码助手、工具决策器）|明确角色定位，约束语言风格（如“专业、简洁、无多余解释”）|
|Few-shot 少样本|结构化转换（如自然语言→JSON）|提供2+示例，统一输入输出格式|
|思维链（CoT）|复杂任务拆解（如多步骤工具调用）|分步引导，明确逻辑框架（如“第一步解析需求，第二步选择工具”）|
|工具调用决策|Agent选择工具|固定输出格式（如JSON），参数清晰（工具名称、输入参数）|
|错误修正|优化Agent输出（如代码报错、格式错误）|指出错误类型，给出修正规则，要求输出修正后内容|
- **核心原则**：精准（避免模糊表述）、强约束（明确输出限制）、新手友好（避免冗余专业术语）。

## 二、实战Prompt示例（Agent常用）

### 示例1：工具调用决策Prompt（Day4/6常用）

```python
prompt = """
【角色】AI Agent决策器
【工具列表】
1. 机票查询：输入参数（city：城市名，date：日期），返回机票最低价格；
2. 酒店查询：输入参数（city：城市名，hotel_name：酒店名），返回酒店价格；
3. 景点查询：输入参数（scenic_name：景点名），返回景点介绍。
【任务】解析用户需求，判断需要调用的工具，输出格式：严格JSON，无其他内容，字段如下：
{"need_tool": true/false, "tool_name": "", "params": {}}
【示例】
用户输入：上海明天的机票？
输出：{"need_tool": true, "tool_name": "机票查询", "params": {"city": "上海", "date": "明天"}}
【现在处理】
用户输入：{user_input}
"""
```

### 示例2：代码助手Prompt（Day5常用）

```python
code_prompt = """
【角色】专业Python代码助手
【任务】根据用户需求，生成可运行、带详细注释的Python代码，基于对话历史修改代码（不重复生成）。
【规则】
1. 代码必须可直接运行，注释清晰（说明函数功能、参数含义）；
2. 用户要求修改代码时，只输出修改后的完整代码+简要说明，无多余内容；
3. 若没有历史代码，直接按需求生成新代码。
【当前对话历史】
{history}
【用户需求】
{input}
"""
```

## 三、今日任务（必做）

1. 熟记Prompt的5要素和5类模板；

2. 编写1个“天气查询工具决策Prompt”，要求输出JSON格式（包含need_tool、tool_name、params）；

3. 编写1个“Python代码助手Prompt”，要求生成带注释的简单脚本（如打印Hello World）。

## 四、常见问题

- Prompt约束不足→LLM输出偏离预期：增加强约束（如“只输出JSON，不添加任何解释、不使用代码块”）；

- 少样本示例不足→LLM识别规律错误：至少提供2个示例，统一输入输出格式。

# Day3：LLM API 调用实战（智谱GLM）

## 一、核心知识点

- **主流免费LLM选择**（新手优先）：
        

    - 智谱GLM：免费额度充足、API调用简单，适配LangChain，本笔记首选；

    - 豆包：需通过火山引擎方舟平台申请，调用方式与智谱类似；

    - 通义千问：需付费，新手不推荐。

- **API调用核心步骤**：
        1. 获取API Key（智谱平台）；
        2. 配置环境变量（存储API Key，避免硬编码）；
        3. 安装智谱SDK；
        4. 调用SDK，解析返回结果。
      

## 二、实战代码（智谱GLM-4-Flash调用）

### 1. 安装智谱SDK

```bash
pip install zhipuai
```

### 2. 配置环境变量（.env文件）

在项目根目录创建 `.env` 文件（文件名固定，无后缀），写入以下内容：

```env
ZHIPU_API_KEY=你的智谱API Key（替换为实际值，从智谱平台获取）
```

### 3. 完整调用代码（day3_glm_api.py）

```python
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

# 加载.env文件中的环境变量（API Key）
load_dotenv()
# 初始化智谱客户端
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 核心函数：调用智谱GLM-4-Flash，返回回答
def call_glm(prompt):
    try:
        # 调用大模型（glm-4-flash为免费模型）
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # 0-1，值越小输出越稳定，代码生成用0
        )
        # 解析返回结果，提取AI回答
        return response.choices[0].message.content
    except Exception as e:
        return f"调用失败：{str(e)}"

# 测试代码
if __name__ == "__main__":
    # 测试普通对话
    print(call_glm("什么是AI Agent？用大白话解释，不超过50字"))
    # 测试代码生成
    print(call_glm("写一个简单的Python打印脚本，带注释"))
```

### 4. 运行验证

```bash
python day3_glm_api.py
```

运行成功后，会输出LLM的回答（普通对话+代码脚本），无报错即说明API调用正常。

## 三、今日任务（必做）

1. 安装zhipuai SDK，配置.env文件，确保API Key正确；

2. 运行上述代码，测试普通对话和代码生成功能；

3. 修改代码，实现“输入一个数学问题，返回计算结果+步骤”。

## 四、常见问题与避坑

- `ModuleNotFoundError: No module named 'sniffio'`：安装依赖：`pip install sniffio`；

- `未提供api_key`：检查.env文件名（必须是.env，而非zhipu.env）、变量名是否为`ZHIPU_API_KEY`；

- API调用报错“额度不足”：智谱平台领取免费额度，或切换glm-4-flash（免费）模型。

# Day4：结构化输出（JSON）与工具调用入门

## 一、核心知识点

- **结构化输出的意义**：AI Agent调用工具时，需要“机器可解析”的格式（纯文本无法被代码识别），JSON是最常用的格式——实现“自然语言→JSON→工具调用”的闭环。

- **结构化输出实现方法**（3步）：
        1. Prompt强约束：明确要求LLM输出JSON，禁止Markdown代码块、多余解释；
        2. 结果清洗：去除LLM输出中可能的````json`标记、空格等冗余内容；
        3. 异常处理：捕获JSON解析失败的情况，避免程序崩溃。
      

- **Agent工具调用闭环**：用户输入（自然语言）→ LLM解析（生成JSON）→ 代码解析JSON → 调用工具 → 返回结果给用户。

## 二、实战代码（JSON解析+工具调用）

### 完整代码（day4_json_tool_call.py）

```python
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os
import json

# 加载环境变量，初始化智谱客户端
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# ---------------------- 模拟工具函数（后续Day6替换为真实工具） ----------------------
def query_flight(city, date):
    """模拟机票查询工具：返回模拟价格"""
    return f"✅ {date}从{city}出发的机票最低价格：500元（经济舱）"

def query_weather(city):
    """模拟天气查询工具：返回模拟天气"""
    return f"✅ {city}今日天气：晴，温度18-28℃，微风"

# 工具映射表：工具名称→工具函数（核心，后续扩展工具只需添加这里）
TOOL_MAP = {
    "机票查询": query_flight,
    "天气查询": query_weather
}

# ---------------------- 核心逻辑：自然语言→JSON→工具调用 ----------------------
def agent_tool_call(user_input):
    # 1. 构造Prompt（强约束JSON输出）
    prompt = f"""
    【角色】AI Agent决策器
    【任务】解析用户需求，生成严格的JSON格式，无任何多余内容、无代码块，字段如下：
    {{
        "need_tool": true/false,  # 是否需要调用工具
        "tool_name": "",          # 工具名称（机票查询/天气查询/无）
        "params": {{}}            # 工具参数（机票查询需city、date；天气查询需city）
    }}
    【示例】
    用户输入：上海明天的机票价格
    输出：{{"need_tool":true,"tool_name":"机票查询","params":{{"city":"上海","date":"明天"}}}}
    用户输入：你好
    输出：{{"need_tool":false,"tool_name":"无","params":{{}}}}
    【用户输入】
    {user_input}
    """

    # 2. 调用LLM，获取决策结果（JSON）
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # 输出稳定，避免格式错乱
    )

    # 3. 清洗结果（去除可能的冗余内容）
    raw_content = response.choices[0].message.content.strip()
    clean_content = raw_content.replace("```json", "").replace("```", "").strip()

    # 4. 解析JSON，调用工具
    try:
        json_data = json.loads(clean_content)
        need_tool = json_data.get("need_tool", False)
        tool_name = json_data.get("tool_name", "无")
        params = json_data.get("params", {})

        if need_tool and tool_name in TOOL_MAP:
            # 动态调用工具（传入参数）
            tool_result = TOOL_MAP[tool_name](**params)
            return f"执行结果：\n{tool_result}"
        else:
            # 无需调用工具，直接让LLM回答
            return client.chat.completions.create(
                model="glm-4-flash",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.7
            ).choices[0].message.content
    except json.JSONDecodeError as e:
        return f"❌ 解析失败（格式错误）：{e}\n请重新输入需求"
    except Exception as e:
        return f"❌ 工具调用失败：{e}"

# 测试代码
if __name__ == "__main__":
    print("🎯 工具调用Agent已启动，输入'退出'结束～")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        print(f"Agent：{agent_tool_call(user_input)}")
```

### 运行验证

```bash
python day4_json_tool_call.py
```

测试场景：
    1. 输入“北京今日天气”→ 调用天气查询工具，返回模拟结果；
    2. 输入“广州后天的机票”→ 调用机票查询工具，返回模拟结果；
    3. 输入“你好”→ 无需调用工具，直接返回LLM回答。

## 三、今日任务（必做）

1. 运行上述代码，测试3个场景，确保JSON解析和工具调用正常；

2. 新增“景点查询”工具（模拟函数，返回景点介绍），更新TOOL_MAP和Prompt；

3. 优化异常处理，当参数缺失时（如只输入“机票查询”，未说城市），提示用户补充信息。

## 四、常见问题

- JSON解析失败：LLM输出带````json`标记 → 代码中添加清洗逻辑，Prompt强化“禁止使用代码块”；

- 工具调用逻辑错误：检查TOOL_MAP中工具名称与JSON中的tool_name是否一致，参数是否匹配；

- 参数缺失：在Prompt中添加“若参数缺失，params字段留空”，代码中判断参数是否完整，提示用户补充。

# Day5：Agent 记忆功能（上下文联动，适配LangChain 0.2.15）

## 一、核心知识点

- **记忆的意义**：之前的工具调用是“单次交互”，添加记忆后，Agent能记住对话历史，实现“连续交互”（如先让Agent写计算器，再让它修改代码，Agent能基于历史代码调整）。

- **LangChain 记忆组件（适配0.2.15版本）**：
        

    - `ConversationBufferMemory`：存储全部对话历史，简单易上手（本笔记首选）；

    - `ConversationSummaryMemory`：总结对话历史，减少Prompt长度（适合长对话，可选）。

- **实现逻辑**：Memory组件存储对话历史 → 每次调用LLM时，自动将历史传入 → LLM基于上下文生成回答。

- **关键导入路径（适配0.2.15，重点！）**：
        

    - ChatZhipuAI：`from langchain_community.chat_models import ChatZhipuAI`

    - ConversationBufferMemory：`from langchain.memory import ConversationBufferMemory`

    - ConversationChain：`from langchain.chains import ConversationChain`

    - ChatPromptTemplate：`from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder`

## 二、实战代码（2个核心demo，均适配0.2.15）

### demo1：基础记忆功能（day5_memory_demo1.py）

```python
from langchain_community.chat_models import ChatZhipuAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 1. 初始化大模型（智谱GLM-4-Flash）
llm = ChatZhipuAI(
    api_key=zhipu_api_key,
    model="glm-4-flash",
    temperature=0.7  # 适度灵活，保留记忆连贯性
)

# 2. 初始化记忆组件（存储对话历史）
memory = ConversationBufferMemory(
    return_messages=True,  # 返回消息对象，更易处理
    memory_key="history"   # 记忆变量名，与Prompt对应
)

# 3. 初始化对话链（整合LLM + 记忆）
conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True  # 开启详细日志，可查看传递给LLM的完整Prompt（含历史）
)

# 4. 交互式对话（带记忆）
def chat_with_memory():
    print("🎉 带记忆的AI助手已启动，输入'退出'结束对话～")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        try:
            # 调用对话链，自动整合历史+新输入
            response = conversation_chain.run(input=user_input)
            print(f"AI：{response}")
        except Exception as e:
            print(f"❌ 运行出错：{str(e)}")
            memory.clear()  # 出错时重置记忆，避免影响后续对话
            print("🔄 已重置记忆，请重新提问")

# 运行对话
if __name__ == "__main__":
    chat_with_memory()
```

### demo2：代码助手+记忆（day5_memory_demo2.py）

```python
from langchain_community.chat_models import ChatZhipuAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 1. 初始化大模型（代码生成用temperature=0，保证准确性）
llm = ChatZhipuAI(
    api_key=zhipu_api_key,
    model="glm-4-flash",
    temperature=0
)

# 2. 初始化记忆组件（专门存储代码对话历史）
memory = ConversationBufferMemory(return_messages=True, memory_key="history")

# 3. 构建自定义Prompt（替代废弃的get_default_prompt，适配0.2.15）
code_prompt = ChatPromptTemplate.from_messages([
    ("system", """
你是一个专业的Python代码助手，严格遵守以下规则：
1. 生成的代码必须可运行、带详细注释，格式规范；
2. 必须基于对话历史修改代码，不要重复生成完整代码；
3. 用户要求修改代码时，只输出修改后的完整代码+简要说明，不要无关内容；
4. 若没有历史代码，直接按用户需求生成新代码。
    """),
    MessagesPlaceholder(variable_name="history"),  # 自动注入对话历史
    ("human", "{input}")  # 自动注入用户新输入
])

# 4. 初始化对话链（整合LLM+记忆+自定义Prompt）
conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=code_prompt,
    verbose=True
)

# 5. 交互式代码助手（带记忆）
def code_chat_with_memory():
    print("🎯 带记忆的Python代码助手已启动（输入'退出'结束）～")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        try:
            response = conversation_chain.run(input=user_input)
            print(f"\n代码助手：\n{response}")
        except Exception as e:
            print(f"❌ 执行出错：{str(e)}")
            memory.clear()
            print("🔄 已重置记忆，请重新输入需求")

# 运行代码助手
if __name__ == "__main__":
    code_chat_with_memory()
```

## 三、运行验证步骤

### 1. 安装LangChain相关依赖（适配0.2.15）

```bash
pip install langchain==0.2.15 langchain-community==0.2.15
```

### 2. 测试demo1（基础记忆）

```bash
python day5_memory_demo1.py
```

测试流程：
    1. 输入“你好，我叫小明，我喜欢Python”；
    2. 再输入“我刚才告诉你我的名字和爱好了吗？”；
    3. AI能准确回答（记住名字和爱好），说明记忆生效。

### 3. 测试demo2（代码助手+记忆）

```bash
python day5_memory_demo2.py
```

测试流程：
    1. 输入“写一个Python计算器，实现加减乘除”→ AI生成基础代码；
    2. 输入“给这个计算器加个平方功能”→ AI基于历史代码修改，添加平方功能，不重复生成完整代码。

## 四、今日任务（必做）

1. 安装LangChain 0.2.15版本，运行两个demo，验证记忆功能；

2. 修改demo1，添加“查看记忆”“清空记忆”功能；

3. 测试demo2，让AI先生成读取文件的脚本，再让它添加“统计文件行数”功能。

## 五、常见问题与避坑（重点！）

- `AttributeError: 'ConversationChain' object has no attribute 'get_default_prompt'`：LangChain 0.2.x 已移除该方法，改用`ChatPromptTemplate`构建Prompt（参考demo2）；

- `ImportError: cannot import name 'ConversationBufferMemory' from 'langchain_community.memory'`：0.2.15版本中，该类在`langchain.memory`下，导入路径为`from langchain.memory import ConversationBufferMemory`；

- 记忆丢失：每次运行代码都会重置内存（临时记忆），Day6会实现“持久化记忆”（文件存储）；

- 对话历史过长：替换为`ConversationSummaryMemory`（总结历史，减少Prompt长度），导入路径：`from langchain.memory import ConversationSummaryMemory`。

# Day6：记忆持久化与工具扩展（真实工具对接）

## 一、核心目标

从Day5的“内存级临时记忆”升级为“文件级持久化记忆”（重启程序不丢失），并扩展Agent能力，对接**真实外部工具**（天气API、文件操作），让Agent具备长期记忆和实用功能。

## 二、前置准备（新增依赖）

```bash
pip install requests  # 调用外部API（如天气API）
pip install pandas    # 可选，处理文件数据（如CSV读取）
```

## 三、任务1：记忆持久化（文件存储，JSON格式）

### 1. 实现思路

- 用`json`模块将对话历史保存到本地JSON文件；

- 程序启动时，自动加载历史记忆；

- 对话结束时，自动保存最新记忆；

- 新增“查看记忆”“清空记忆”功能，提升实用性。

### 2. 完整代码（day6_memory_persist.py）

```python
import json
import os
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0.7)

# 持久化存储路径（项目根目录，文件名可自定义）
MEMORY_FILE = "agent_memory.json"

# ---------------------- 记忆操作核心函数 ----------------------
def load_memory():
    """加载历史记忆（从文件读取到内存）"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)  # 读取JSON格式的对话历史
        except json.JSONDecodeError:
            print("⚠️ 记忆文件损坏，已重置为空记忆")
            return []
    # 若文件不存在，返回空列表（无历史记忆）
    return []

def save_memory(memory_list):
    """保存最新记忆（从内存写入文件）"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False：支持中文，indent=2：格式化JSON，便于查看
        json.dump(memory_list, f, ensure_ascii=False, indent=2)

def clear_memory():
    """清空所有记忆（删除记忆文件）"""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    print("✅ 所有记忆已清空")

def show_memory():
    """查看当前所有记忆（对话历史）"""
    memory = load_memory()
    if not memory:
        print("📝 当前无对话记忆")
        return
    print("📝 对话历史记忆：")
    for msg in memory:
        # 区分用户和AI的消息
        role = "你" if msg["role"] == "user" else "AI"
        print(f"{role}：{msg['content']}")

# ---------------------- 带持久化记忆的对话核心函数 ----------------------
def chat_with_persistent_memory(user_input):
    """加载记忆→调用LLM→保存记忆，实现持久化"""
    # 1. 加载历史记忆
    memory = load_memory()
    # 2. 将新的用户输入添加到记忆中
    memory.append({"role": "user", "content": user_input})
    
    # 3. 调用LLM（基于历史记忆生成回答）
    try:
        response = llm.invoke(memory)  # 传入全部记忆，实现上下文联动
        ai_answer = response.content
    except Exception as e:
        ai_answer = f"❌ 调用失败：{str(e)}"
        return ai_answer
    
    # 4. 将AI的回答添加到记忆中，保存到文件
    memory.append({"role": "assistant", "content": ai_answer})
    save_memory(memory)
    
    return ai_answer

# ---------------------- 交互式对话入口 ----------------------
def main():
    print("🎯 带持久化记忆的AI Agent已启动～")
    print("🔧 支持操作：输入'退出'结束，'查看记忆'查看历史，'清空记忆'重置记忆")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        elif user_input == "清空记忆":
            clear_memory()
            continue
        elif user_input == "查看记忆":
            show_memory()
            continue
        
        # 核心对话逻辑
        answer = chat_with_persistent_memory(user_input)
        print(f"AI：{answer}")

if __name__ == "__main__":
    main()
```

### 3. 测试验证

```bash
python day6_memory_persist.py
```

测试流程：
    1. 输入“我叫小红，我在学习AI Agent”；
    2. 关闭程序，重新运行；
    3. 输入“我刚才告诉你我的名字了吗？”；
    4. AI能准确回答（记忆从文件加载，未丢失）；
    5. 输入“查看记忆”，能看到之前的对话；输入“清空记忆”，记忆被重置。

## 四、任务2：工具扩展（对接真实外部工具）

### 1. 实现思路

- 定义真实工具函数（天气查询、文件读写）；

- 构建“工具名称-函数”映射表（TOOL_MAP），便于动态调用；

- 让LLM解析用户需求，决策是否调用工具、调用哪个工具、传入什么参数；

- 整合工具执行结果，返回给用户，实现“需求→工具→结果”的闭环。

### 2. 完整代码（day6_tool_extension.py）

```python
import json
import os
import requests
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 初始化配置
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0)

# ---------------------- 1. 定义真实工具函数 ----------------------
def query_weather(city):
    """真实天气查询（对接免费天气API，无需申请Key）"""
    if not city:
        return "❌ 未指定城市，无法查询天气"
    try:
        # 免费天气API（稳定可用，无需注册）
        url = f"https://api.vvhan.com/api/weather?city={city}"
        res = requests.get(url, timeout=5)  # 超时时间5秒，避免卡住
        res.raise_for_status()  # 抛出HTTP错误（如404、500）
        data = res.json()
        
        if data.get("success") != True:
            return f"❌ 天气查询失败：{data.get('msg', '未知错误')}"
        
        # 提取关键天气信息（简化输出）
        weather = data["data"]["weather"]
        tem = data["data"]["tem"]
        wind = data["data"]["wind"]
        return f"✅ {city}今日天气：{weather}，温度：{tem}℃，风向：{wind}"
    except requests.exceptions.Timeout:
        return "❌ 天气API请求超时，请检查网络"
    except Exception as e:
        return f"❌ 天气查询出错：{str(e)}"

def write_file(file_path, content):
    """文件写入工具（本地文件，支持绝对路径/相对路径）"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件已成功写入：{os.path.abspath(file_path)}"
    except Exception as e:
        return f"❌ 文件写入失败：{str(e)}"

def read_file(file_path):
    """文件读取工具（读取本地文件内容）"""
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{os.path.abspath(file_path)}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"✅ 文件内容：\n{content}"
    except Exception as e:
        return f"❌ 文件读取失败：{str(e)}"

# ---------------------- 2. 工具映射表（核心，扩展工具只需添加这里） ----------------------
TOOL_MAP = {
    "天气查询": query_weather,
    "文件写入": write_file,
    "文件读取": read_file
}

# ---------------------- 3. 工具决策函数（让LLM解析需求，决定调用哪个工具） ----------------------
def decide_tool(user_input):
    """
    让LLM解析用户需求，返回JSON格式的决策结果：
    {"need_tool": true/false, "tool_name": "", "params": {}}
    """
    prompt = f"""
    【角色】AI Agent工具决策器
    【任务】严格解析用户需求，返回JSON格式结果，无任何多余内容、无代码块，字段必须完整：
    {{
        "need_tool": true/false,  # 是否需要调用工具（是/否）
        "tool_name": "",          # 工具名称（天气查询/文件写入/文件读取/无）
        "params": {{}}            # 工具参数（对应工具的输入参数，缺失则留空）
    }}
    【工具列表及参数说明】
    1. 天气查询：必须传入参数 city（城市名，如北京、上海）；
    2. 文件写入：必须传入参数 file_path（文件路径）、content（写入内容）；
    3. 文件读取：必须传入参数 file_path（文件路径）；
    【示例】
    用户输入：北京今日天气
    输出：{{"need_tool":true,"tool_name":"天气查询","params":{{"city":"北京"}}}}
    用户输入：把'Hello AI Agent'写入test.txt
    输出：{{"need_tool":true,"tool_name":"文件写入","params":{{"file_path":"test.txt","content":"Hello AI Agent"}}}}
    用户输入：你好
    输出：{{"need_tool":false,"tool_name":"无","params":{{}}}}
    【用户输入】
    {user_input}
    """
    # 调用LLM获取决策结果
    response = llm.invoke(prompt)
    # 清洗结果（去除可能的冗余内容）
    clean_res = response.content.strip().replace("```json", "").replace("```", "")
    try:
        return json.loads(clean_res)
    except json.JSONDecodeError:
        # 解析失败时，返回无需调用工具
        return {"need_tool": False, "tool_name": "无", "params": {}}

# ---------------------- 4. 核心Agent逻辑（整合工具决策+工具调用） ----------------------
def ai_agent(user_input):
    """完整工具扩展Agent：解析需求→调用工具→返回结果"""
    # 第一步：工具决策
    decision = decide_tool(user_input)
    
    # 第二步：调用工具（若需要）
    if decision["need_tool"] and decision["tool_name"] in TOOL_MAP:
        tool_func = TOOL_MAP[decision["tool_name"]]
        try:
            # 动态调用工具，传入参数（**params 解包字典）
            tool_result = tool_func(**decision["params"])
        except Exception as e:
            tool_result = f"❌ 工具调用失败：{str(e)}"
        return tool_result
    else:
        # 无需调用工具，直接让LLM回答
        return llm.invoke(user_input).content

# ---------------------- 5. 交互式入口 ----------------------
def main():
    print("🎯 带工具扩展的AI Agent已启动（输入'退出'结束）～")
    print("🔧 支持工具：")
    print("  1. 天气查询：输入'城市+今日天气'（如：广州今日天气）")
    print("  2. 文件写入：输入'把XX写入XX文件'（如：把测试内容写入test.txt）")
    print("  3. 文件读取：输入'读取XX文件'（如：读取test.txt）")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        result = ai_agent(user_input)
        print(f"Agent：{result}")

if __name__ == "__main__":
    main()
```

### 3. 测试验证

```bash
python day6_tool_extension.py
```

测试场景（必做）：
    1. 输入“上海今日天气”→ 调用真实天气API，返回上海当日天气；
    2. 输入“把'AI Agent Day6 工具扩展测试'写入agent_test.txt”→ 生成对应文件；
    3. 输入“读取agent_test.txt”→ 返回文件内容；
    4. 输入“你好”→ 无需调用工具，直接返回LLM回答。

## 五、任务3：整合记忆持久化+工具扩展（完整Agent）

### 完整代码（day6_full_agent.py）

```python
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

# ---------------------- 记忆模块（复用Day6任务1的核心函数） ----------------------
def load_memory():
    return json.load(open(MEMORY_FILE, "r", encoding="utf-8")) if os.path.exists(MEMORY_FILE) else []

def save_memory(memory):
    json.dump(memory, open(MEMORY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------------- 工具模块（复用Day6任务2的核心函数） ----------------------
# 工具函数
def query_weather(city):
    try:
        url = f"https://api.vvhan.com/api/weather?city={city}"
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("success"):
            return f"✅ {city}今日天气：{data['data']['weather']}，温度：{data['data']['tem']}℃"
        return f"❌ 天气查询失败：{data.get('msg')}"
    except Exception as e:
        return f"❌ 天气查询出错：{str(e)}"

def write_file(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 文件写入成功：{file_path}"
    except Exception as e:
        return f"❌ 文件写入失败：{str(e)}"

def read_file(file_path):
    if not os.path.exists(file_path):
        return f"❌ 文件不存在：{file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f"✅ 文件内容：\n{f.read()}"
    except Exception as e:
        return f"❌ 文件读取失败：{str(e)}"

# 工具映射表
TOOL_MAP = {
    "天气查询": query_weather,
    "文件写入": write_file,
    "文件读取": read_file
}

# 工具决策函数
def decide_tool(user_input, memory):
    prompt = f"""
    基于对话历史：{json.dumps(memory, ensure_ascii=False)}
    解析用户需求：{user_input}
    返回严格JSON，无多余内容：{{"need_tool":true/false,"tool_name":"","params":{{}}}}
    工具列表：天气查询（city）、文件写入（file_path,content）、文件读取（file_path）
    """
    clean_res = llm.invoke(p
```
> （注：文档部分内容可能由 AI 生成）