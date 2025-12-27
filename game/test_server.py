import sys
import os

from zmq_client_server.server_router import RouterServer

if __name__ == "__main__":
    # --- 步驟 1: 確保 Python 找得到 RL 資料夾 ---
    # 獲取當前文件 (test_server.py) 的絕對路徑
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    # 獲取上一層目錄 (Balancing_Ball_for_RL 根目錄)
    project_root = os.path.dirname(current_dir)

    # 如果根目錄不在系統搜尋路徑中，將其加入
    if project_root not in sys.path:
        sys.path.append(project_root)


    connect_string = "tcp://localhost:5555"
    router_server = RouterServer(num_levels=1,
                                 level=4,
                                 setup_mode="train",
                                 connect_string=connect_string,
                                 )
    
    router_server.start()