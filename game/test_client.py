import multiprocessing
import time

from zmq_client_server.client_human import GameClientHuman


if __name__ == "__main__":
    fps = 100
    server_addr = "tcp://localhost:5555"
    
    client_id1 = "human_client1"
    client1 = GameClientHuman(
        client_id=client_id1,
        fps=fps,
        server_addr=server_addr,
    )
    
    client_id2 = "human_client2"
    client2 = GameClientHuman(
        client_id=client_id2,
        fps=fps,
        server_addr=server_addr,
    )

    p1 = multiprocessing.Process(target=client1.start, daemon=True)
    p2 = multiprocessing.Process(target=client2.start, daemon=True)

    p1.start()
    p2.start()

    print("進程已啟動。按 Ctrl+C 退出...")

    try:
        while True:
            # 每 1 秒醒來一次，檢查子進程是否還活著
            # 這段時間足夠短，讓你能感覺到 Ctrl+C 是即時的
            time.sleep(1)
            
            # 如果所有子進程都意外退出了，主程序也可以退出了
            if not p1.is_alive() and not p2.is_alive():
                break

    except KeyboardInterrupt:
        print("\n檢測到 Ctrl+C！正在終止子進程...")
        
        # 雖然 daemon=True 會在主進程結束時殺死它們
        # 但顯式調用 terminate 能確保資源更快釋放（特別是在 Windows 上）
        p1.terminate() 
        p2.terminate()
        
        # 等待它們徹底死透
        p1.join()
        p2.join()
        print("已安全退出。")