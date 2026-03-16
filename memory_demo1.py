from langchain_community.chat_models import ChatZhipuAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 初始化大模型
llm = ChatZhipuAI(
    api_key=zhipu_api_key,
    model="glm-4-flash",
    temperature=0.7
)

# 初始化记忆组件
memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="history"
)

# 初始化对话链
conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 交互式对话
def chat_with_memory():
    print("🎉 带记忆的AI助手已启动，输入'退出'结束对话～")
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "退出":
            print("👋 再见！")
            break
        response = conversation_chain.run(input=user_input)
        print(f"AI：{response}")

if __name__ == "__main__":
    chat_with_memory()