import pymunk
import pygame
import time
import os
import numpy as np
import sys

from PIL import Image
from typing import Optional
# from IPython.display import ipd, display, Image, clear_output

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
 
from script.record import Recorder
from script.levels.get_levels import get_level
from script.levels.levels import Levels
from script.collision_handle import CollisionHandler
from script.role.player import Player
from script.role.platform import Platform
from script.role.roles import Role
from script.levels.rewards.reward_calculator import RewardCalculator
from script.game_config import GameConfig
from script.renderer import ModernGLRenderer
from exceptions import GameClosedException

class BalancingBallGame:
    """
    A physics-based balancing ball game that can run standalone or be used as a Gym environment.
    """
    # Game constants

    # Visual settings for indie style
    BACKGROUND_COLOR: tuple  # Dark blue background TODO Hard code

    def __init__(self,
                 BACKGROUND_COLOR = (41, 50, 65),
                 render_mode: str = None,
                 obs_width: int = 160,
                 obs_height: int = 160,
                 sound_enabled: bool = True,
                 max_episode_step: int = None,
                 collision_type: dict = None,
                 player_configs: dict = None,
                 platform_configs: dict = None,
                 environment_configs: dict = None,
                 level_config_path: str = None,
                 level: int = None,
                 capture_per_second: int = None,
                 is_enable_realistic_field_of_view_cropping: bool = False,
                ):
        """
        Initialize the balancing ball game.

        Args:
            render_mode: "human" for visible window, "headless" for gym env
            sound_enabled: Whether to enable sound effects
            max_episode_step: 1 step = 1/fps, if fps = 120, 1 step = 1/120
            capture_per_second: save game screen as a image every second, None means no capture
            is_enable_realistic_field_of_view_cropping: With the realistic field of view mechanism enabled, characters will have their own field of view and will not be able to see things outside that field of view or that are obstructed.
        """
        # Game parameters
            
        self.BACKGROUND_COLOR=BACKGROUND_COLOR
        self.BACKGROUND_COLOR_RL = (0,0,0)
        self.self_color_RL = (0,255,0)
        self.enemy_color_RL = (255,0,0)
        self.obs_width = obs_width
        self.obs_height = obs_height
            
        self.max_episode_step = max_episode_step

        self.recorder = Recorder("game_history_record")
        self.render_mode = render_mode
        self.sound_enabled = sound_enabled
        self.human_control = None

        self.space = pymunk.Space()
        self.level: Levels = get_level(
            level=level, 
            game=self,
            collision_type=collision_type, 
            player_configs=player_configs, 
            platform_configs=platform_configs, 
            environment_configs=environment_configs,
            level_config_path=level_config_path
        )
        self.window_x = GameConfig.SCREEN_WIDTH
        self.window_y = GameConfig.SCREEN_HEIGHT
        self.fps = GameConfig.FPS
        self.collision_handler = CollisionHandler(self.space)
        self.capture_per_second = capture_per_second
        if capture_per_second:
            self.capture_per_second = capture_per_second * self.fps
            os.makedirs("./capture/", exist_ok=True)

        self.setup_pygame()

        self.players: list[Player]
        self.platforms: list[Platform]
        self.entities: list[Role]
        self.ability_generated_objects: list[Role] = []
        self.reward_calculator: RewardCalculator
        self.players, self.platforms, self.entities, self.reward_calculator = self.level.setup()
        self.num_players = len(self.players)

        # Initialize physics space

        self.collision_handler.set_players(self.players)
        self.collision_handler.set_platforms(self.platforms)
        self.collision_handler.set_entities(self.entities)
        self.collision_handler.setup_default_collision_handlers() # 只调用一次！

        # Game state tracking
        self.steps = 0
        self.start_time = time.time()
        self.end_time = self.start_time
        self.game_over = False
        self.score = {p.role_id: 0 for p in self.players}  # Total Score for each player
        self.winner = None
        self.last_speeds = [0] * self.num_players  # Track last speed for each player
        self.step_rewards = {p.role_id: 0 for p in self.players}  # Rewards obtained in the last step
        self.step_action = None
        self.is_enable_realistic_field_of_view_cropping = is_enable_realistic_field_of_view_cropping
        if self.is_enable_realistic_field_of_view_cropping:
            raise NotImplementedError("realistic_field_of_view_cropping not implement yet.")

        # Create folders for captures if needed
        # CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        CURRENT_DIR = "."
        os.makedirs(os.path.dirname(CURRENT_DIR + "/capture/"), exist_ok=True)

    def setup_pygame(self):
        """Set up PyGame and ModernGL"""
        pygame.init()
        self.frame_count = 0
        self.render_fps_counter = 0      # 當前秒內的幀數計數
        self.render_fps_timer = time.time() # 上一次更新 FPS 的時間
        self.current_render_fps = 0.0    # 用於顯示的 FPS 數值

        if self.sound_enabled:
            self._load_sounds()

        # 設置 OpenGL 標誌
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        
        if self.render_mode == "human":
            self.screen = pygame.display.set_mode((self.window_x, self.window_y), flags)

            pygame.display.set_caption("Balancing Ball - ModernGL")
            # 初始化渲染器
            self.mgl = ModernGLRenderer(self.window_x, self.window_y, obs_width=self.obs_width, obs_height=self.obs_height, headless=False)
            
            # 文字使用 Pygame Font，但渲染方式會改變
            self.font = pygame.font.Font(None, int(self.window_x / 34))
            # 創建一個純 Pygame Surface 用於繪製 UI/文字
            self.ui_surface = pygame.Surface((self.window_x, self.window_y), pygame.SRCALPHA)

        elif self.render_mode == "headless":
            self.mgl = ModernGLRenderer(self.window_x, self.window_y, headless=True)
            if self.capture_per_second:
                self.screen = pygame.Surface((self.window_x, self.window_y))

        elif self.render_mode == "server":
            # 返回坐標到客戶端，沒有需要設置的東西
            pass

        else:
            raise ValueError(f"Invalid render mode: {self.render_mode}. Choose from 'human', 'server', 'headless'")

        self.clock = pygame.time.Clock()

    def _load_sounds(self):
        """Load game sound effects"""
        try:
            pygame.mixer.init()
            self.sound_bounce = pygame.mixer.Sound("assets/bounce.wav") if os.path.exists("assets/bounce.wav") else None
            self.sound_fall = pygame.mixer.Sound("assets/fall.wav") if os.path.exists("assets/fall.wav") else None

            if not self.sound_bounce or not self.sound_fall:
                print("Sound files not found, disabling sound.")
                self.sound_enabled = False
        except Exception:
            print("Sound loading error")
            self.sound_enabled = False
            pass

    def reset(self) -> np.ndarray:
        """Reset the game state and return the initial observation"""
        # Reset physics objects
        self.level.reset()
        self.reward_calculator.reset()

        # Reset game state
        self.steps = 0
        self.start_time = time.time()
        self.game_over = False
        self.score = {p.role_id: 0 for p in self.players}
        self.winner = None
        self.last_speeds = [0] * self.num_players

    def step(self, pactions: dict):
        """
        Take a step in the game using the given actions.

        Args:
            actions: List of continuous actions [-1.0, 1.0] for each player controlling horizontal force

        Returns:
            observation: Game state observation
            rewards: List of rewards for each player
            terminated: Whether episode is done
            info: Additional information
        """

        self.level.status_reset_step()

        # Step the physics simulation
        self.space.step(1/self.fps)

        # 在物理糢擬后執行動作會導致環境數據過時，但是當 FPS 較高時，這種影響可以忽略不計
        # 而且不得不這麽做的原因是碰撞檢測的回調函數只能在 step 之後執行
        
        # 需要保留直到移除舊模型，詳情看函數說明
        # actions = pactions if isinstance(pactions, list) else [pactions]
        # actions = self.calculate_player_speed_old(actions)
        self.step_action = pactions
        if pactions:
            for player in self.players:
                try:
                    if pactions[player.role_id]:
                        self.ability_generated_objects.extend(player.perform_action(pactions[player.role_id], self.steps))
                except KeyError:
                    continue
        self.add_step(1)
        rewards, terminated = self.reward()
        self.step_rewards = rewards
        self.handle_update_each_frame()

        rewards, terminated = self.level.action(rewards, terminated)

        return rewards, terminated 

    def reward(self):
        """
        Calculate and return the reward for the current state.
        """

        # 和玩家存活相關的檢查必須在最上面，因爲後續獎勵計算依賴於玩家是否存活
        rewards, alive_count = self.reward_calculator.calculate_rewards()
        # if self.sound_enabled and self.sound_fall and num_of_players_fell_this_step > 0:
        #     self.sound_fall.play()

        # 處理玩家與實體的碰撞獎勵，包含每個 Step 的狀態重設

        # Check if game should end
        terminated = False
        if alive_count == 0 or (alive_count == 1 and self.num_players > 1) or self.steps >= self.max_episode_step:
            terminated = True
            self.game_over = True

            # Determine winner (last player alive or highest score)
            if alive_count == 1 and self.num_players > 1:
                self.winner = next(p for p in self.players if p.get_is_alive()) 
                # Give bonus to winner
                self.winner.add_reward_per_step(0.5 * self.steps / 100)  # 生存時間越長獎勵越多 TODO Hard code
                self.score[self.winner.role_id] += self.winner.get_reward_per_step()
            elif self.steps == self.max_episode_step:
                # Game ended due to max steps, winner is highest score
                self.winner = np.argmax(self.score)
            else:
                self.winner = None

        rewards = {}
        for player in self.players:
            rewards[player.role_id] = player.get_reward_per_step()
            self.score[player.role_id] += rewards[player.role_id]

        if self.game_over:
            result = {
                "game_total_duration": f"{time.time() - self.start_time:.2f}",
                "scores": self.score,
                "winner": self.winner.role_id,
                "steps": self.steps
            }
            self.recorder.add_no_limit(result)

        return rewards, terminated

    def _get_observation_game_screen(self) -> dict[np.ndarray, np.ndarray]:
        """Convert game state to observation for RL agent"""
        # update particles and draw them

        if isinstance(self.capture_per_second, int | float):
            if self.frame_count % self.capture_per_second == 0:  # Every second at 60 FPS
                pixels = self.screen_data # 得到 (H, W, 1) 的 numpy 數組
                if isinstance(pixels, dict):
                    for key, pixel in pixels.items():
                        img_to_save = pixel.squeeze() 

                        # 轉換為 Image 對象並保存 (mode='L' 表示 8-bit 灰階)
                        Image.fromarray(img_to_save).save(f"capture/frame_{key}_{self.frame_count/60}.png")
                        print(f"圖片已保存為 capture/frame_{self.frame_count/60}.png")
                else:
                    img_to_save = pixel.squeeze() 

                    # 轉換為 Image 對象並保存 (mode='L' 表示 8-bit 灰階)
                    Image.fromarray(img_to_save).save(f"capture/frame_{key}_{self.frame_count/60}.png")
                    print(f"圖片已保存為 capture/frame_{self.frame_count/60}.png")
            self.frame_count += 1

        return self.screen_data
    
    def _get_observation_state_based(self) -> np.ndarray:
        """Public method to get the current observation without taking a step"""
        obs = self.level._get_observation_state_based()

        return obs

    def render(self) -> Optional[np.ndarray]:
        """Render the current game state"""
        
        if self.render_mode == "server":
            self.screen_data = {}
            for p in self.players:
                self.screen_data[p.role_id] = self.calculate_verts(p.role_id)
            return None
        
        # 3. 繪製 UI (文字)
        if self.render_mode == "human":

            self.render_fps_counter += 1
            current_time = time.time()
            time_diff = current_time - self.render_fps_timer
            if time_diff >= 0.1: # 每秒更新一次
                self.current_render_fps = self.render_fps_counter / time_diff
                self.render_fps_counter = 0
                self.render_fps_timer = current_time

                # total_entities = len(self.players) + len(self.platforms) + len(self.ability_generated_objects)
                # print(F"FPS: {int(self.current_render_fps)}, total_steps: {self.steps}")

            # 清空 UI 層
            self.mgl.fbo_render_human.use()
            self.mgl.clear(self.BACKGROUND_COLOR_RL, self.BACKGROUND_COLOR)
            poly_verts, circle_batch = self.calculate_verts()
            self._draw_scene_moderngl(poly_verts, circle_batch)
            self.ui_surface.fill((0,0,0,0)) 
            self._draw_game_info_to_surface(self.ui_surface)
            self.mgl.draw_texture(self.ui_surface)
            pygame.display.flip()

        # output for RL
        self.mgl.fbo_render_rl.use()
        self.mgl.clear(self.BACKGROUND_COLOR_RL, self.BACKGROUND_COLOR)
        self.screen_data = {}
        for p in self.players:
            poly_verts, circle_batch = self.calculate_verts(p.role_id)
            self._draw_scene_moderngl(poly_verts, circle_batch)
            self.screen_data[p.role_id] = self.mgl.read_pixels()
        return None

    def calculate_verts(self, player_role_id = None):

        # 準備數據容器
        # 圓形數據: [x, y, radius, r, g, b]
        circle_batch = []
        
        # 多邊形數據: [x, y, r, g, b, a]
        # 我們直接構建一個大列表，最後再一次性轉 numpy
        poly_verts = []
        # 預先定義常數以加速訪問
        to_color = lambda c: (c[0]/255, c[1]/255, c[2]/255)
        
        # 收集所有實體
        all_entities = []
        # 這裡根據你的遊戲邏輯，只選活著的或者存在的
        if player_role_id:
            for p in self.players:
                if p.role_id == player_role_id:
                    p.color_rl = self.self_color_RL
                    target_digit = p.get_collision_type() % 1000
                else:
                    p.color_rl = self.enemy_color_RL
                    
                if p.get_is_alive(): 
                    all_entities.append(p)
            
            for obj in self.ability_generated_objects:
                if obj.get_collision_type() % 1000 == target_digit:
                    obj.color_rl = self.self_color_RL
                else:
                    obj.color_rl = self.enemy_color_RL
                all_entities.append(obj)
                
        else:
            for p in self.players:
                if p.get_is_alive(): 
                    all_entities.append(p)
            all_entities.extend(self.ability_generated_objects)


        all_entities.extend(self.platforms)
        for obj_list in self.entities: # 假設 self.entities 是列表的列表
            all_entities.extend(obj_list)

        for entity in all_entities:
            shape = entity.shape.shape
            body = entity.shape.body
            color_norm = to_color(entity.color_rl) if player_role_id else to_color(entity.color)

            if isinstance(shape, pymunk.Circle):
                # 圓形：只需提取位置和半徑
                pos = body.position
                # 添加數據: x, y, radius, r, g, b
                circle_batch.append([pos.x, pos.y, shape.radius, *color_norm])
                
                # 如果需要繪製旋轉指示線 (Line)，將其視為細長的多邊形處理
                if entity.shape.is_draw_rotation_indicator:
                    # 計算線段端點
                    vec = pymunk.Vec2d(shape.radius, 0).rotated(body.angle)
                    end = pos + vec
                    # 線段稍微粗一點，這裡簡化為線段繪製 (或者用 GL_LINES)
                    # 這裡為了簡單，我們忽略線段的寬度優化，或者你可以把它加到 poly_verts 裡
                    # 為了極致效能，RL訓練時通常不需要這個視覺細節，建議註釋掉
                    pass 

            elif isinstance(shape, pymunk.Poly):
                # 多邊形：獲取世界坐標頂點
                # Pymunk 的 get_vertices 是局部坐標，需要轉換
                # 這裡是一個潛在的 CPU 瓶頸，如果物體不變形，可以緩存 world vertices
                pts = [body.local_to_world(v) for v in shape.get_vertices()]
                
                # 簡單的三角剖分 (Triangle Fan -> Triangles)
                # 假設凸多邊形，中心點為 pts[0]
                c_r, c_g, c_b = color_norm
                root = pts[0]
                for i in range(1, len(pts) - 1):
                    # 每個三角形由 root, pts[i], pts[i+1] 組成
                    p1, p2 = pts[i], pts[i+1]
                    # 展開頂點數據 [x, y, r, g, b, a] * 3
                    poly_verts.extend([
                        root.x, root.y, c_r, c_g, c_b, 1.0,
                        p1.x,   p1.y,   c_r, c_g, c_b, 1.0,
                        p2.x,   p2.y,   c_r, c_g, c_b, 1.0
                    ])
            
            elif isinstance(shape, pymunk.Segment):
                # ➖ 線段：轉換為矩形多邊形
                a = body.local_to_world(shape.a)
                b = body.local_to_world(shape.b)
                r = shape.radius if shape.radius > 0 else 1.0
                # 計算法線方向
                delta = b - a
                normal = pymunk.Vec2d(-delta.y, delta.x).normalized() * r
                
                v1 = a + normal
                v2 = a - normal
                v3 = b - normal
                v4 = b + normal
                
                c_r, c_g, c_b = color_norm
                # 兩個三角形組成一個矩形
                poly_verts.extend([
                    v1.x, v1.y, c_r, c_g, c_b, 1.0,
                    v2.x, v2.y, c_r, c_g, c_b, 1.0,
                    v3.x, v3.y, c_r, c_g, c_b, 1.0,
                    v1.x, v1.y, c_r, c_g, c_b, 1.0,
                    v3.x, v3.y, c_r, c_g, c_b, 1.0,
                    v4.x, v4.y, c_r, c_g, c_b, 1.0
                ])
        return poly_verts, circle_batch

    def _draw_scene_moderngl(self, poly_verts, circle_batch):
        """ModernGL 繪製流程"""

        # 繪製所有多邊形
        if poly_verts:
            # 轉換為 numpy array (float32)
            v_data = np.array(poly_verts, dtype='f4')
            self.mgl.render_polygons(v_data.tobytes(), len(poly_verts) // 6)

        # 繪製所有圓形
        if circle_batch:
            self.mgl.render_circles(circle_batch)

    def _draw_game_info_to_surface(self, target_surface):
        """
        Draw game information onto a specific surface (used for ModernGL texture overlay).
        Args:
            target_surface: A pygame.Surface with SRCALPHA flag enabled.
        """
        # 1. 準備文字內容
        time_text = f"Time: {self.end_time - self.start_time:.1f}, steps: {self.steps}/{self.max_episode_step}"
        fps_text = f"FPS: {int(self.current_render_fps)}"
        score_texts = [f"{player.role_id}: {self.score[player.role_id]:.1f} + {self.step_rewards[player.role_id]} Health: {player.get_health():.1f}" for player in self.players]

        # 2. 渲染文字本身
        time_surface = self.font.render(time_text, True, (255, 255, 255))
        fps_surface = self.font.render(fps_text, True, (200, 255, 200))
        score_surfaces = [self.font.render(text, True, (255, 255, 255)) for text in score_texts]

        # 3. 繪製 Time (背景 + 文字) -> 改用 target_surface
        pygame.draw.rect(target_surface, (0, 0, 0, 128),
                        (5, 5, time_surface.get_width() + 10, time_surface.get_height() + 5))
        target_surface.blit(time_surface, (10, 10))

        # 4. 繪製 FPS -> 改用 target_surface
        pygame.draw.rect(target_surface, (0, 0, 0, 128),
                        (5, 40, fps_surface.get_width() + 10, fps_surface.get_height() + 5))
        target_surface.blit(fps_surface, (10, 40))

        # 5. 繪製 Scores -> 改用 target_surface
        y_offset = 75
        for i, surface in enumerate(score_surfaces):
            color = self.players[i].get_color() if self.players[i].get_is_alive() else (100, 100, 100)
            
            # 繪製半透明背景
            pygame.draw.rect(target_surface, (0, 0, 0, 128),
                            (5, y_offset, surface.get_width() + 10, surface.get_height() + 5))
            
            # 重新渲染帶顏色的文字 (因為原本 score_texts 只是字串，這裡為了變色需要重繪或優化)
            # 原本代碼邏輯是這裡才變色，所以保持原樣：
            colored_surface = self.font.render(score_texts[i], True, color)
            target_surface.blit(colored_surface, (10, y_offset))
            y_offset += 30

        # 6. 處理 Game Over 畫面
        if self.game_over:
            if self.winner is not None:
                game_over_text = f"WINNER: Player {self.winner.role_id} - Press R to restart"
            elif self.num_players == 1:
                game_over_text = "GAME OVER - Press R to restart"
            elif self.steps == self.max_episode_step:
                game_over_text = f"Time limit reached. Winner by score: Player {self.winner.role_id}"
            else:
                game_over_text = "DRAW - Press R to restart"

            print("Final Scores: ", self.score, " total step: ", self.steps) 
            print(game_over_text)
            game_over_surface = self.font.render(game_over_text, True, (255, 255, 255))

            # 繪製全螢幕半透明遮罩
            # 直接畫在 target_surface 上即可，因為它是蓋在 3D 場景上的
            overlay = pygame.Surface((self.window_x, self.window_y), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            target_surface.blit(overlay, (0, 0))

            # 繪製 Game Over 文字
            target_surface.blit(game_over_surface,
                           (self.window_x/2 - game_over_surface.get_width()/2,
                            self.window_y/2 - game_over_surface.get_height()/2))
        else:
            self.end_time = time.time()

    def close(self):
        """Close the game and clean up resources"""
        pygame.quit()
            
    def calculate_player_speed_old(self, moving_direction: list = []):
        """
        Calculate the speed of the player ball

        新訓練的模型是連續動作空間，範圍包含正數和負數，
        但是早期訓練的模型只能輸出 0 和 1，分別代表向左和向右，因此有必要保留這個函數直到移除舊模型
        """
        # In order to fit the model action space, the model can currently only output 0 and 1, so 2 is no action

        for i in range(len(moving_direction)):
            if moving_direction[i] == 0:
                moving_direction[i] = pymunk.Vec2d(self.players[i].get_speed() * -1, 0)

            elif moving_direction[i] == 1:
                moving_direction[i] = pymunk.Vec2d(self.players[i].get_speed(), 0)

            elif moving_direction[i] == 2:
                moving_direction[i] = pymunk.Vec2d(0, 0)

            else:
                raise ValueError(f"Invalid action: {moving_direction}. Action must be 0 (left), 1 (right), or 2 (no action).")
            
            # 遍歷所有玩家
        for i, player in enumerate(self.players):
            # 如果 actions 列表不夠長，則對後續玩家使用 0 作為預設動作
            force_vector = moving_direction[i]
            player.move(force_vector)

    def run_standalone(self, players_id):
        """Run the game in standalone mode with keyboard controls"""
        try:
            from human_control import HumanControl
        except ImportError:
            from script.human_control import HumanControl
            
        self.human_control = HumanControl(self)
        self.assign_players(player_id_list=[players_id])

        self.run = True
        while self.run:
            # Handle events
            actions = self.human_control.get_player_actions()

            # Take game step
            if not self.game_over:
                rewards, terminated = self.step(actions)

        self.close()
        
    def handle_update_each_frame(self) -> bool:
        """
        處理 Pygame 事件。
        如果偵測到關閉事件，則清理 Pygame 資源並引發一個自訂異常。
        """
        self.render()

        # 從後往前遍歷。這樣刪除後方的元素不會影響前方尚未遍歷的索引。
        for i in range(len(self.ability_generated_objects) - 1, -1, -1):
            obj = self.ability_generated_objects[i]
            if obj.expired_time <= 0:
                obj.remove_from_space()
                self.ability_generated_objects.pop(i) # 根據索引安全刪除
            else:
                obj.expired_time -= 1

        if self.render_mode == "human":
            # 讓游戲幀率不超過設定幀率
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Close button pressed. Signaling for graceful shutdown.")
                    self.close()  # 關閉 Pygame
                    self.run = False
                    raise GameClosedException("User closed the game window.") # <--- 修改點

    def assign_players(self, player_id_list: list[str]):
        RL_player_id = "RL_player"
        RL_player_num = 0
        for p in self.players:
            if player_id_list:
                p.role_id = player_id_list.pop(0)
            else:
                RL_player_num += 1
                p.role_id = f"{RL_player_id}{RL_player_num}"
            print(f"{p.role_id} assigned")
            if "human" in p.role_id.lower() and self.human_control == None:
                try:
                    from human_control import HumanControl
                except ImportError:
                    from script.human_control import HumanControl
                    
                self.human_control = HumanControl(self)

        self.score = {p.role_id: 0 for p in self.players}  # Total Score for each player
        self.step_rewards = {p.role_id: 0 for p in self.players} 

        if len(player_id_list) > 0: 
            print(f"The following players are not assigned: {player_id_list}")


    def add_step(self, steps: int = None):
        self.steps += steps

    def get_players(self):
        return self.players
    
    def get_num_players(self):
        return self.num_players
    
    def get_platforms(self):
        return self.platforms
    
    def get_entities(self):
        return self.entities
    
    def get_game_over(self):
        return self.game_over
    
    def get_space(self):
        return self.space

    def get_collision_handler(self):
        return self.collision_handler

    def get_step(self):
        return self.steps
    
    def get_fps(self):
        return self.fps
    
    def get_step_action(self):
        return self.step_action

    def set_step_rewards(self, rewards: list):
        self.step_rewards = rewards