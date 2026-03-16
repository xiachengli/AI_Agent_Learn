import json
import os
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
zhipu_api_key = os.getenv("ZHIPU_API_KEY")

# 持久化存储路径（自定义，建议放在项目根目录）
MEMORY_FILE = "agent_memory.json"
# 初始化大模型
llm = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4-flash", temperature=0.7)

# ---------------------- 记忆操作核心函数 ----------------------
def load_memory():
    """加载历史记忆（文件→内存）"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ 记忆文件损坏，已重置为空")
            return []
    return []

def save_memory(memory_list):
    """保存最新记忆（内存→文件）"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_list, f, ensure_ascii=False, indent=2)

def clear_memory():
    """清空所有记忆"""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    print("✅ 记忆已清空")

def show_memory():
    """查看当前记忆"""
    memory = load_memory()
    if not memory:
        print("📝 当前无记忆")
        return
    print("📝 对话历史记忆：")
    for msg in memory:
        role = "你" if msg["role"] == "user" else "AI"
        print(f"{role}：{msg['content']}")

# ---------------------- 带持久化记忆的对话 ----------------------
def chat_with_persistent_memory(user_input):
    """核心对话函数：加载记忆→调用LLM→保存记忆"""
    # 1. 加载历史记忆
    memory = load_memory()
    # 2. 添加新的用户输入到记忆
    memory.append({"role": "user", "content": user_input})
    
    # 3. 调用LLM（基于历史记忆生成回答）
    try:
        response = llm.invoke(memory)
        ai_answer = response.content
    except Exception as e:
        ai_answer = f"❌ 调用失败：{str(e)}"
        return ai_answer
    
    # 4. 保存AI回答到记忆
    memory.append({"role": "assistant", "content": ai_answer})
    save_memory(memory)
    
    return ai_answer

# ---------------------- 交互式对话入口 ----------------------
def main():
    print("🎯 带持久化记忆的AI Agent已启动（输入'退出'结束，'清空记忆'/'查看记忆'执行对应操作）～")
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