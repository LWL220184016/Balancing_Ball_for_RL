import sys
import os
import multiprocessing
import time

from zmq_client_server.server_router import RouterServer
from zmq_client_server.client_human import GameClientHuman

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
    
    client_id1 = "human_client1"
    fps = 100
    server_addr = "tcp://localhost:5555"
    client1 = GameClientHuman(client_id=client_id1,
                              fps=fps,
                              server_addr=server_addr,
                             )
    
    client_id2 = "human_client2"
    client2 = GameClientHuman(client_id=client_id2,
                              fps=fps,
                              server_addr=server_addr,
                             )
    
    守護進程不能創建子進程，需要在這裏添加啓動關卡子進程
    rp1 = multiprocessing.Process(target=router_server.start, daemon=True)
    cp1 = multiprocessing.Process(target=client1.start, daemon=True)
    cp2 = multiprocessing.Process(target=client2.start, daemon=True)

    rp1.start()
    time.sleep(5)
    # 目前在路由服務器進入客戶端分配階段前啓動客戶端可能導致報錯，不清楚爲什麽
    cp1.start()
    cp2.start()

    print("進程已啟動。按 Ctrl+C 退出...")

    try:
        while True:
            # 每 1 秒醒來一次，檢查子進程是否還活著
            # 這段時間足夠短，讓你能感覺到 Ctrl+C 是即時的
            time.sleep(1)
            
            # 如果所有子進程都意外退出了，主程序也可以退出了
            if not rp1.is_alive() and not cp1.is_alive() and not cp2.is_alive():
                break

    except KeyboardInterrupt:
        print("\n檢測到 Ctrl+C！正在終止子進程...")
        
        # 雖然 daemon=True 會在主進程結束時殺死它們
        # 但顯式調用 terminate 能確保資源更快釋放（特別是在 Windows 上）
        rp1.terminate() 
        cp1.terminate() 
        cp2.terminate()
        
        # 等待它們徹底死透
        rp1.join()
        cp1.join()
        cp2.join()
        print("已安全退出。")
