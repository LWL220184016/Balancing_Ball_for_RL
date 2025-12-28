import zmq
import multiprocessing
import time
import pickle
import os
import signal
import sys
import importlib

from zmq_client_server.level_process import start_level
from zmq_client_server.warning_msg import msg_router, warning_msg_not_expect_type

class RouterServer:
    def __init__(self, connect_string: str="ipc:///tmp/zmq_router_pipe", num_levels: int=None, level: int=None, setup_mode: str=None):
        """
        Docstring for __init__
        
        :param self: Description
        :param connect_string: Description
        :type connect_string: str
        :param num_levels: Description
        :type num_levels: int
        :param level: Description
        :type level: int
        :param setup_mode: Description
        :type setup_mode: str
        """

        self.connect_string = connect_string
        self.num_levels = num_levels
        self.level = level
        match setup_mode:
            case "test":
                self.setup = self.setup_for_testing
            case "train":
                self.setup = self.setup_for_training
        
        # 清理舊的 IPC 文件，防止地址已佔用錯誤
        if "ipc://" in self.connect_string:
            ipc_path = self.connect_string.replace("ipc://", "")
            if os.path.exists(ipc_path):
                os.remove(ipc_path)

        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind(self.connect_string)

        self.client_to_level = {}
        self.level_to_clients = {f"level{level}_{i}": {"player_num": None, "client": [], "process": None} for i in range(num_levels)}
        
        # 用於標記伺服器是否正在運行
        self.is_running = True
        self.current_task = ""

        # --- 註冊信號處理，預防 Ctrl+C 留下僵尸進程 ---
        signal.signal(signal.SIGINT, self._handle_exit_signal)
        signal.signal(signal.SIGTERM, self._handle_exit_signal)


    def start(self):
        try:
            # 設置接收超時
            self.router.setsockopt(zmq.RCVTIMEO, 2000) # 2秒超時，方便循環檢查 is_running

            self.setup()

            # 本地緩存，性能優化
            pass

            # 3. 主循環
            msg_router("Training Loop Started.")
            self.current_task = "訓練進行中"
            while self.is_running:
                try:
                    address, _, msg_type, data = self.router.recv_multipart()
                    sender_id = address.decode()
                    
                    if msg_type == b"ACTION_RL" or msg_type == b"ACTION_HUMAN":
                        level_id = self.client_to_level.get(sender_id)
                        if level_id:
                            self.router.send_multipart([level_id.encode(), b"", msg_type, data])
                    
                    elif msg_type == b"OBS":
                        # 這裡只需要做一次 loads，解開外層字典
                        payload = pickle.loads(data) 
                        for client_id, pre_pickled_bytes in payload.items():
                            self.router.send_multipart([
                                client_id.encode(), b"", b"OBS_DATA", pre_pickled_bytes
                            ])
                    
                    else:
                        warning_msg_not_expect_type(sender_id=sender_id, msg_type=msg_type, payload=payload)

                except zmq.Again:
                    continue
                except Exception as e:
                    msg_router(f"執行任務：{self.current_task} 的過程中出現錯誤: {e}.")
                    import traceback
                    traceback.print_exc()
                    break

        finally:
            self.shutdown()

    def setup_for_testing(self):
        func_name = sys._getframe().f_code.co_name
        class_name = self.__class__.__name__
        raise NotImplementedError(f"Method '{class_name}.{func_name}' is not implemented")

    def setup_for_training(self):
        

        if self._is_running_in_colab():
            msg_router("目前運行在 Google Colab 中，因爲一次只能運行一個代碼塊，主進程需要分給 Ray rillib，子進程不能在作爲守護進程的情況下生成孫子進程，但是不使用守護進程將容易在主進程報錯停機的情況下產生多個僵尸進程。")
            msg_router("因此運行在 Google Colab 中的時候，路由服務器進程將不會創建環境子進程，所有子進程統一在 Ray rillib 的 Trainer 進程創建。")
        else:
            self.run_level_subprocess()
        num_level_finish_init = 0
        num_level_finish_player_assign = 0
        num_level_finish_setup = 0
        client_id_cache_list = []
        client_setup_data_cache_list = {f"level{self.level}_{i}": None for i in range(self.num_levels)}

        # 等待 LEVEL_PLAYER_NUM (加入子進程存活檢查) ----------------------------------------------------------------------------
        self.current_task = "等待 LEVEL_PLAYER_NUM"
        while num_level_finish_init < self.num_levels and self.is_running:
            try:
                address, _, msg_type, data = self.router.recv_multipart()
                sender_id = address.decode()
                payload = pickle.loads(data)

                if msg_type == b"LEVEL_MAX_PLAYER_NUM":
                    self.level_to_clients[sender_id]["player_num"] = payload
                    num_level_finish_init += 1
                elif msg_type == b"CLIENT_JOIN":
                    client_id_cache_list.append(sender_id)
                else: 
                    warning_msg_not_expect_type(task=self.current_task, sender_id=sender_id, msg_type=msg_type, payload=payload)
            except zmq.Again:
                msg_router(f"Level {self.current_task} Timeout! Still waiting for {self.num_levels - num_level_finish_player_assign} levels...")
                # 檢查子進程是否還活著，預防啟動階段就有子進程崩潰導致死等
                for lid, info in self.level_to_clients.items():
                    if not info["process"].is_alive() and info["player_num"] is None:
                        msg_router(f"{lid} crashed during setup!")
                        self.shutdown()
                        return
                continue
        msg_router("所有關卡初始化完畢，開始分配客戶端...")
        # ---------------------------------------------------------------------------------------------------------------------

        # 分配客戶端到有空餘的關卡環境 -------------------------------------------------------------------------------------------
        self.current_task = "分配客戶端到有空餘的關卡環境"
        for key, value in self.level_to_clients.items():
            while len(value["client"]) < value["player_num"] and self.is_running:
                # 緩存還不是空的，先用完緩存
                if client_id_cache_list:
                    client_id = client_id_cache_list.pop(0)
                # 緩存是空的，等新 client 接入
                else:
                    try:
                        address, empty, msg_type, data = self.router.recv_multipart()
                        sender_id = address.decode()
                        if msg_type == b"LEVEL_SETUP":
                            # 不需要 pickle.loads，路由服務器不需要知道裏面有什麽，而且等一下就轉發到客戶端了
                            client_setup_data_cache_list[sender_id] = data
                            continue
                        elif msg_type != b"CLIENT_JOIN":
                            payload = pickle.loads(data)
                            warning_msg_not_expect_type(task=self.current_task, sender_id=sender_id, msg_type=msg_type, payload=payload)
                            continue
                        
                        client_id = sender_id
                    except zmq.Again:
                        msg_router(f"Level {self.current_task} Timeout! Still waiting for {self.num_levels - num_level_finish_player_assign} levels...")
                        continue
                
                self.client_to_level[client_id] = key
                value["client"].append(client_id)
                # 給關卡環境進程發客戶端 ID 是爲了更好分辨玩家之間輸出的動作
                self.router.send_multipart([key.encode(), b"", b"CLIENT_ASSIGN", pickle.dumps(client_id)])
                msg_router(f"Assigned {client_id} to {key}")
            num_level_finish_player_assign += 1
        msg_router("分配客戶端完畢，開始把設置信息返回給對應客戶端...")
        # ---------------------------------------------------------------------------------------------------------------------

        # 返回各種物件的設置信息到客戶端 ----------------------------------------------------------------------------------------
        self.current_task = "返回各種物件的設置信息到客戶端"
        while num_level_finish_setup < self.num_levels:
            has_processed = False # 標記這一輪有沒有處理數據
            try:
                address, _, msg_type, data = self.router.recv_multipart()
                sender_id = address.decode()
                if msg_type == b"LEVEL_SETUP":
                    # 不需要 pickle.loads，路由服務器不需要知道裏面有什麽，而且等一下就轉發到客戶端了
                    client_setup_data_cache_list[sender_id] = data
                else: 
                    warning_msg_not_expect_type(task=self.current_task, sender_id=sender_id, msg_type=msg_type, payload=payload)
                
                # 同樣要用 list() 副本
                for key in list(client_setup_data_cache_list.keys()):
                    if client_setup_data_cache_list[key] is None:
                        continue # 跳過，等待下次循環看它有沒有變
                    
                    # 發現數據！取出並移除
                    value = client_setup_data_cache_list.pop(key)
                    for client_id in self.level_to_clients[key]["client"]:
                        self.router.send_multipart([client_id.encode(), b"", b"CLIENT_SETUP", value])

                    has_processed = True
                    num_level_finish_setup += 1
                
                if not has_processed:
                    # 如果這一輪全是 None，休息一下避免 CPU 飆高到 100%
                    # 模擬等待其他線程/進程寫入數據到 client_setup_data_cache_list[key]
                    time.sleep(0.01) 
                    
            except zmq.Again:
                msg_router(f"Level {self.current_task} Timeout! Still waiting for {self.num_levels - num_level_finish_player_assign} levels...")
                continue

        msg_router("已經把所以設置信息返回給對應客戶端，路由服務器設置完畢")

        # ---------------------------------------------------------------------------------------------------------------------

    def run_level_subprocess(self):
        
        # 啟動 Level 子進程
        module_path = f"RL.levels.level{self.level}.model1.config"
        
        try:
            imported_module = importlib.import_module(module_path)
            self.train_config = imported_module.train_config
            self.model_config = imported_module.model_config
        except ImportError as e:
            msg_router(f"錯誤：找不到 Level {self.level} 的配置文件或是路徑錯誤。")
            msg_router(f"嘗試路徑: {module_path}")
            raise e
        except AttributeError as e:
            msg_router(f"錯誤：在 Level {self.level} 的 config.py 中找不到 model_config 或 train_config。")
            raise e

        for i in range(self.num_levels):
            msg_router(f"創建關卡環境{i} 子進程中")
            level_id = f"level{self.level}_{i}"
            p = multiprocessing.Process(
                target=start_level, 
                args=(level_id, self.connect_string, self.level, self.train_config.total_timesteps, self.model_config.level_config_path),
                daemon=True # 設置為守護進程，主進程死掉時子進程通常會被系統回收
            )
            p.start()
            self.level_to_clients[level_id]["process"] = p

    def _handle_exit_signal(self, signum, frame):
        msg_router(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        """優雅關閉所有資源"""
        self.is_running = False
        msg_router("Terminating sub-processes...")
        for level_id, info in self.level_to_clients.items():
            p = info.get("process")
            if p and p.is_alive():
                msg_router(f" - Terminating {level_id} (PID: {p.pid})")
                p.terminate()  # 先嘗試正常終止
        
        # 等待一小段時間讓子進程回收
        time.sleep(0.5)
        
        for level_id, info in self.level_to_clients.items():
            p = info.get("process")
            if p and p.is_alive():
                p.kill() # 如果還沒死，強制殺掉
            if p:
                p.join() # 徹底回收進程表項目，預防僵尸進程

        self.router.close()
        self.context.term()
        
        if "ipc://" in self.connect_string:
            ipc_path = self.connect_string.replace("ipc://", "")
            if os.path.exists(ipc_path):
                os.remove(ipc_path)
        msg_router("Cleanup complete.")

    def _is_running_in_colab(self):
        return 'google.colab' in sys.modules
    
if __name__ == "__main__":
    router_server = RouterServer(num_levels=1,
                                 level=1,
                                 setup_mode="train"
                                 )