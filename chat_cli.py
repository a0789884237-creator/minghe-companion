"""交互式聊天脚本。"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def chat(message: str, user_id: str = "user1") -> dict:
    """发送聊天请求。"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": user_id, "message": message}
    )
    return response.json()

def main():
    print("=" * 50)
    print("明禾陪伴 - 心理资讯大师")
    print("=" * 50)
    print("输入 'quit' 或 '退出' 结束对话")
    print("-" * 50)
    
    user_id = input("请输入用户名: ").strip() or "user1"
    
    while True:
        message = input("\n你: ").strip()
        
        if message in ["quit", "退出", "q"]:
            print("再见！祝你一切安好。")
            break
        
        if not message:
            continue
        
        try:
            result = chat(message, user_id)
            print(f"\n明禾: {result['response']}")
            print(f"[意图: {result['intent']} | 风险: {result['risk_level']}]")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    main()
