from langchain_community.chat_models import ChatZhipuAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 1. 初始化大模型
llm = ChatZhipuAI(
    api_key=zhipu_api_key,
    model="glm-4-flash",
    temperature=0
)

# 2. 初始化记忆组件
memory = ConversationBufferMemory(return_messages=True, memory_key="history")

# 3. 用 ChatPromptTemplate 构建自定义 Prompt（替代 get_default_prompt）
code_prompt = ChatPromptTemplate.from_messages([
    ("system", """
你是一个专业的Python代码助手，严格遵守以下规则：
1. 生成的代码必须可运行、带详细注释，格式规范；
2. 必须基于对话历史修改代码，不要重复生成完整代码；
3. 用户要求修改代码时，只输出修改后的完整代码+简要说明，不要无关内容；
4. 若没有历史代码，直接按用户需求生成新代码。
    """),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# 4. 初始化对话链（整合LLM+记忆+自定义Prompt）
conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=code_prompt,
    verbose=True
)

# 5. 交互式代码助手
def code_chat_with_memory():
    print("🎯 带记忆的Python代码助手已启动（输入'退出'结束对话）～")
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

if __name__ == "__main__":
    code_chat_with_memory()