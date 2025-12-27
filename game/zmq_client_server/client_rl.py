import zmq
import multiprocessing
import time
import pickle
import os
import gymnasium as gym
import numpy as np

from schema_to_gym_space import schema_to_gym_space

class GameClientRL:
    def __init__(self, client_id, server_addr="ipc:///tmp/zmq_router_pipe"):
        self.client_id = client_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt_string(zmq.IDENTITY, f"CLIENT_{client_id}")
        self.socket.connect(server_addr)
        self.action_space = None

    def run(self):
        # 本地緩存，性能優化
        socket = self.socket

        # 1. 請求加入
        print(f"[Client {self.client_id}] Joining...")
        socket.send_multipart([b"", b"CLIENT_JOIN", pickle.dumps(None)])

        _, msg_type, data = socket.recv_multipart()
        
        if msg_type == b"CLIENT_SETUP":
            payload = pickle.loads(data)
            print("Received Action Space Schema:", payload)
            
            # --- 核心步驟：初始化 Action Space ---
            self.action_space = schema_to_gym_space(payload)
            print("Initialized Gym Action Space:", self.action_space)


        while True:
            # 2. 接收觀察數據
            _, msg_type, data = socket.recv_multipart()
            if msg_type == b"OBS_DATA":
                obs = pickle.loads(data)
                self.render(obs)
                
                # 3. 發送動作 (範例動作)
                action = {"force": 10.5, "direction": 1}
                socket.send_multipart([b"", b"ACTION", pickle.dumps(action)])

    def render(self, obs):
        # 在這裡進行畫面渲染，obs 只含有真實視野的數據
        # print(f"[Client {self.client_id}] Rendering FOV: {obs}")
        pass

