import os

# --- 顏色定義 ---
class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"       # 亮綠色 (Router)
    PURPLE = "\033[95m"      # 亮紫色 (Level)
    LIGHT_BLUE = "\033[94m"  # 亮藍色 (Client)

# Windows 系統有時需要執行這行才能正常顯示 ANSI 顏色
if os.name == 'nt':
    os.system('')

def msg_router(msg):
    # 綠色
    print(f"{Colors.GREEN}[Router] {msg}{Colors.RESET}", flush=True) 

def msg_level(level_id, msg):
    # 紫色
    print(f"{Colors.PURPLE}[Level {level_id}] {msg}{Colors.RESET}", flush=True) 

def msg_client(client_id, msg):
    # 淺藍色 (注意：我將參數名改為了 client_id 以更符合語意，你可以改回 level_id)
    print(f"{Colors.LIGHT_BLUE}[Client {client_id}] {msg}{Colors.RESET}", flush=True)

def warning_msg_not_expect_type(task, sender_id, msg_type, payload):
    print(f"warning: [task: {task}]Received not expect message, sender_id: {sender_id}, msg_type: {msg_type}, payload: {payload}", flush=True)
    
# --- 測試代碼 ---
if __name__ == "__main__":
    msg_router("服務器啟動中...")
    msg_level(1, "關卡環境初始化完成")
    msg_client("human_1", "玩家已加入")
    print("這是一行沒有顏色的普通輸出。")