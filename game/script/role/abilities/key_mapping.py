import pygame

class KeyMapping:
    # 使用字典儲存字串與 Pygame 鍵位常數的映射
    Keyborad_Mappings = {
        # 因爲使用了 lower()，所以這裡的鍵名全部使用小寫
        "a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c, "d": pygame.K_d, "e": pygame.K_e,
        "f": pygame.K_f, "g": pygame.K_g, "h": pygame.K_h, "i": pygame.K_i, "j": pygame.K_j,
        "k": pygame.K_k, "l": pygame.K_l, "m": pygame.K_m, "n": pygame.K_n, "o": pygame.K_o,
        "p": pygame.K_p, "q": pygame.K_q, "r": pygame.K_r, "s": pygame.K_s, "t": pygame.K_t,
        "u": pygame.K_u, "v": pygame.K_v, "w": pygame.K_w, "x": pygame.K_x, "y": pygame.K_y,
        "z": pygame.K_z,

        # 數字鍵
        "0": pygame.K_0, "1": pygame.K_1, "2": pygame.K_2, "3": pygame.K_3, "4": pygame.K_4,
        "5": pygame.K_5, "6": pygame.K_6, "7": pygame.K_7, "8": pygame.K_8, "9": pygame.K_9,

        # 功能鍵
        "esc": pygame.K_ESCAPE,
        "space": pygame.K_SPACE,
        "enter": pygame.K_RETURN,
        "backspace": pygame.K_BACKSPACE,
        "tab": pygame.K_TAB,
        "shift": pygame.K_LSHIFT,
        "ctrl": pygame.K_LCTRL,
        "alt": pygame.K_LALT,

        # 方向鍵
        "arrow_up": pygame.K_UP,
        "arrow_down": pygame.K_DOWN,
        "arrow_left": pygame.K_LEFT,
        "arrow_right": pygame.K_RIGHT,

    }

    Mouse_Mappings = {
        "left": 0,
        "middle": 1,
        "right": 2,
        "scroll_up": 3,
        "scroll_down": 4
    }

    @classmethod
    def get(cls, keys: dict | list | str, default=None):
        """
        安全獲取鍵位的方法
        例如: KeyMapping.get("a") -> 返回 pygame.K_a
        """
        if isinstance(keys, list):
            for i in range(len(keys)):
                keys[i] = cls.Keyborad_Mappings.get(keys[i].lower(), default)
        
        elif isinstance(keys, dict):
            for key, key_list in keys["keyboard"].items():
                keys["keyboard"][key] = [cls.Keyborad_Mappings.get(key_str.lower(), default) for key_str in key_list]

            for key, key_list in keys["mouse"].items():
                keys["mouse"][key] = [cls.Mouse_Mappings.get(key_str.lower(), default) for key_str in key_list]
                
        elif isinstance(keys, str):
            keys = cls.Keyborad_Mappings.get(keys.lower(), default)

        else:
            raise TypeError("KeyMapping.get only accepts str, list, or dict types.")
        
        return keys

# 使用範例:
# if event.key == KeyMapping.get("A"):
#     print("按下了 A 鍵")

if __name__ == "__main__":
    pygame.init()
    # print("KeyMapping.Keyborad_Mappings:", KeyMapping.Keyborad_Mappings)
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("KeyMapping Example")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == KeyMapping.get("a"):
                    print("按下了 A 鍵")
                elif event.key == KeyMapping.get("space"):
                    print("按下了 空格 鍵")

    pygame.quit()