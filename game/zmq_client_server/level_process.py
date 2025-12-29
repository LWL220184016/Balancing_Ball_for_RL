import zmq
import pickle

from script.balancing_ball_game import BalancingBallGame
from script.game_config import GameConfig
from zmq_client_server.warning_msg import msg_level, warning_msg_not_expect_type

# --- 子進程：環境模擬器 ---
def start_level(level_id, server_addr, level: int, max_episode_step, level_config_path):
    """
    每個 Level 進程負責運行一個 BalancingBallGame 實例
    """

    game = BalancingBallGame(
        render_mode="server",
        sound_enabled=False,
        max_episode_step=max_episode_step,
        level_config_path=level_config_path,
        level=level,
        is_enable_realistic_field_of_view_cropping=False,
    )

    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    # 設置身份，方便 Router 辨識這是哪個環境
    socket.setsockopt_string(zmq.IDENTITY, level_id)
    socket.connect(server_addr)
    socket.send_multipart([b"", b"LEVEL_MAX_PLAYER_NUM", pickle.dumps(GameConfig.PLAYER_NUM)])
    sender_id = "Main_Router_Server"

    assigned_clients = []
    msg_level(level_id, "關卡進程初始化完成，等待路由服務器分配客戶端...")

    while len(assigned_clients) < GameConfig.PLAYER_NUM:
        _, msg_type, data = socket.recv_multipart()

        if msg_type == b"CLIENT_ASSIGN":
            payload = pickle.loads(data)
            assigned_clients.append(payload)
        else:
            warning_msg_not_expect_type(sender_id=sender_id, msg_type=msg_type, payload=payload)

    game.assign_players(assigned_clients)
    
    msg_level(level_id, "客戶端分配完成，發送客戶端設置數據...")
    draw_object = {}
    for obj in game.get_players() + game.get_platforms() + game.get_entities():
        if obj.shape.__class__.__name__.lower() == "circle": # 因爲圓形的 get_size 實際上返回的是半徑，到了客戶端會被當成直徑來初始化，所以要在這裏先變成直徑
            size = obj.get_size() * 2
        else:
            size = obj.get_size()
        draw_object[obj.role_id] = {}
        draw_object[obj.role_id]["size"] = size
        draw_object[obj.role_id]["color"] = obj.get_color()
        draw_object[obj.role_id]["shape_type"] = obj.shape.__class__.__name__.lower()

        for key, ability in obj.get_abilities().items():
            config = ability.ability_generated_object_config
            if config != None:
                obj_key = ability.ability_generated_object_name
                if config["shape_type"].lower() == "circle":
                    size = int(GameConfig.scale_x(config["size"][0]))
                elif config["shape_type"].lower() == "rectangle":
                    size = (GameConfig.scale_x(config["size"][0]), GameConfig.scale_y(config["size"][1]))

                draw_object[obj_key] = {}
                draw_object[obj_key]["size"] = size
                draw_object[obj_key]["color"] = config["color"]
                draw_object[obj_key]["shape_type"] = config["shape_type"]

    setup_data = {
        "client_setup": {
            "action_space": GameConfig.ACTION_SPACE_CONFIG,
            "window_x": GameConfig.SCREEN_WIDTH,
            "window_y": GameConfig.SCREEN_HEIGHT,
            "background_color": game.BACKGROUND_COLOR,
            "draw_object": draw_object
        }
    }
    socket.send_multipart([b"", b"LEVEL_SETUP", pickle.dumps(setup_data)])

    
    msg_level(level_id, "客戶端設置數據發送完成，現在開始游戲...")
    default_action = {}
    game.step(default_action)
    obs_dict = game.screen_data
    msg_level(level_id, f"發送環境觀察數據... \n {obs_dict}")
    # 發送環境觀察回 Router
    # 預先為每個玩家準備好序列化後的字節流
    pre_pickled_obs = {
        cid: pickle.dumps(single_obs_data) for cid, single_obs_data in obs_dict.items()
    }
    # 一次性發送給 Router
    socket.send_multipart([b"", b"OBS", pickle.dumps(pre_pickled_obs)])


    while True:
        # 同步鎖，如果想要解除，可以加入 client_id 然後對應無動作，或者修改 step 邏輯跳過 dict 中沒有的 client_id
        player_actions = {}

        # 接收來自 Router 的消息
        # 格式: [b"CMD", payload]
        while len(player_actions) < GameConfig.PLAYER_NUM:
            _, msg_type, data = socket.recv_multipart()
            payload = pickle.loads(data)

            # msg_level(level_id, f"接收到用戶輸入... \n {payload}")
            if msg_type == b"ACTION_RL":
                player_actions[key] = payload[key]
            elif msg_type == b"ACTION_HUMAN":
                key, item = payload.popitem()
                player_actions[key] = game.human_control.get_player_actions(keyboard_keys=item["keyboard_keys"], mouse_buttons=item["mouse_buttons"], mouse_position=item["mouse_position"])
                # msg_level(level_id, f"轉換後的人類用戶輸入... \n {payload}")
            else:
                warning_msg_not_expect_type(sender_id=sender_id, msg_type=msg_type, payload=payload)

        # 接收到了動作數據 payload = {client_id: action_dict}
        # msg_level(level_id, f"轉換後的人類用戶輸入... \n {player_actions}")
        game.step(player_actions)
        obs_dict = game.screen_data
        # msg_level(level_id, f"發送環境觀察數據... \n {obs_dict}")
        # 發送環境觀察回 Router
        # 預先為每個玩家準備好序列化後的字節流
        pre_pickled_obs = {
            cid: pickle.dumps(single_obs_data) for cid, single_obs_data in obs_dict.items()
        }
        # 一次性發送給 Router
        socket.send_multipart([b"", b"OBS", pickle.dumps(pre_pickled_obs)])

