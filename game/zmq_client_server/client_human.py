import zmq
import pickle
import pygame
import numpy as np

from script.exceptions import GameClosedException
from script.renderer import ModernGLRenderer
from zmq_client_server.warning_msg import msg_client, warning_msg_not_expect_type

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 將導致循環導入的 import 語句移到這裡
    from script.role.shapes.shape import Shape

# --- 類：客戶端 ---
class GameClientHuman:

    def __init__(self, client_id, fps, server_addr="ipc:///tmp/zmq_router_pipe"):
        # __init__ 只保存配置數據，不創建 Socket 或 Pygame 對象
        self.client_id = client_id
        self.fps = fps
        self.server_addr = server_addr
        self.run_flag = True
        self.BACKGROUND_COLOR = None

    def start(self):
        # 在子進程開始運行時，才初始化 ZMQ，Pygame
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.client_id)
        socket.connect(self.server_addr)
        pygame.init() 
        clock = pygame.time.Clock()

        msg_client(self.client_id, f"Joining...")
        socket.send_multipart([b"", b"CLIENT_JOIN", pickle.dumps(None)])

        # 接收配置
        _, msg_type, data = socket.recv_multipart()
        if msg_type == b"CLIENT_SETUP":
            config = pickle.loads(data)
            self.setup(config["client_setup"]) # setup 裡有 set_mode，這是正確的
            pygame.display.set_caption(f"Balancing Ball - {self.client_id}")

        try:
            while self.run_flag:
                # 接收數據
                _, msg_type, data = socket.recv_multipart()
                if msg_type == b"OBS_DATA":
                    obs = pickle.loads(data)
                    self.render(obs, clock) # 傳入 clock
                    
                    keyboard_keys = pygame.key.get_pressed()
                    mouse_buttons = pygame.mouse.get_pressed()
                    mouse_position = pygame.mouse.get_pos() 

                    action = { 
                        self.client_id: { # 這裏加上客戶端 ID 就可以避免在路由服務器解包加入 ID 再封包
                            "keyboard_keys": keyboard_keys, # 轉為 tuple 較安全
                            "mouse_buttons": mouse_buttons,
                            "mouse_position": mouse_position,
                        }
                    }
                    socket.send_multipart([b"", b"ACTION_HUMAN", pickle.dumps(action)])
        
        except Exception as e:
            msg_client(self.client_id, f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理資源
            pygame.quit()
            socket.close()
            context.term()

    def render(self, obs: dict, clock):
        # 在這裡進行畫面渲染，obs 只含有真實視野的數據
        # msg_client(self.client_id, f"Rendering FOV: {obs}")
    
        self.mgl.clear(self.BACKGROUND_COLOR)
        self.mgl.fbo_render_gray.use()
        poly_verts = obs[0]
        circle_batch = obs[1]
        
        # 繪製所有多邊形
        if poly_verts:
            v_data = np.array(poly_verts, dtype='f4')
            self.mgl.render_polygons(v_data.tobytes(), len(poly_verts) // 6)

        # 繪製所有圓形
        if circle_batch:
            self.mgl.render_circles(circle_batch)


        pygame.display.flip()
        clock.tick(self.fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run_flag = False
                # 這裡不要只 raise Exception，因為在子進程中 raise 主進程捕獲不到
                # 最好是設標誌位退出循環，讓 finally 塊處理清理

    def setup(self, config: dict[dict,dict]):
        # 顯示窗口設置
        msg_client(self.client_id, f"收到 Config: {config}")
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((config["window_x"], config["window_y"]), flags=flags)
        self.mgl = ModernGLRenderer(config["window_x"], config["window_y"], headless=False)
        self.font = pygame.font.Font(None, int(config["window_x"] / 34))

        # 初始化需要繪製的物件
        self.BACKGROUND_COLOR = config["background_color"]
        
if __name__ == "__main__":
    client_id = "human_client1"
    fps = 360
    client = GameClientHuman(
        client_id=client_id,
        fps=fps,
    )

    client.start()