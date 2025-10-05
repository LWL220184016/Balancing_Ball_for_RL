問題1：
在 Balancing_Ball_for_RL\game\gym_env.py 的 Function step_state_based 中的這行代碼：
transformed_action = [[action[0], action[1], (abs(action[2] * self.window_x), abs(action[3] * self.window_y))]] 
transformed_action = [[action[0], action[1], (abs(float(action[2] * self.window_x)), abs(float(action[3] * self.window_y)))]]

在這裏，action 是一個 len 為 4 的 List，裏面儲存這 4 個 np.float32 并且範圍在 -1 到 1 内的值。
這是模型輸出的動作，第一個是控制左右行動，第二個控制跳躍，第三個和第四個是控制釋放技能（Collision）的方向。
而 transformed_action 是把他們重組成一個合適的格式來執行動作，下方是在 game\role\abilities\collision.py 中 print 出 velocity_vector 的計算結果。
可以看到，不管有沒有吧 transformed_action 中的 action[2] 和 action[3] 轉換成 float, 他們計算後的 velocity_vector 看起來都非常接近。
可實際上如果不轉換成 float，那麽不管 velocity_vector 的值是多大多小 ( 可以通過修改 abilities_default_cfg 中 Collision 的 speed 來曾加 )
也只會有方向的區別，速度都是一樣，希望有大老解答

np.float32:
Collision ability used. Setting velocity to: Vec2d(-5733.294, -1768.9941)
Collision ability used. Setting velocity to: Vec2d(3621.3713, 4783.897)
Collision ability used. Setting velocity to: Vec2d(-5132.264, -3108.0325)
Collision ability used. Setting velocity to: Vec2d(5666.5693, -1972.3068)
Collision ability used. Setting velocity to: Vec2d(-3368.0212, -4965.5244)
Collision ability used. Setting velocity to: Vec2d(-816.9567, -5944.1216)
Collision ability used. Setting velocity to: Vec2d(-1032.721, -5910.4556)
Collision ability used. Setting velocity to: Vec2d(5723.7515, 1799.6301)
Collision ability used. Setting velocity to: Vec2d(5655.1323, 2004.8647)
Collision ability used. Setting velocity to: Vec2d(4794.107, -3607.8438)
Collision ability used. Setting velocity to: Vec2d(-2053.1372, 5637.786)
Collision ability used. Setting velocity to: Vec2d(2925.4531, -5238.485)
Collision ability used. Setting velocity to: Vec2d(-3434.7556, 4919.5986)
Collision ability used. Setting velocity to: Vec2d(4588.1167, -3866.418)
Collision ability used. Setting velocity to: Vec2d(3461.8574, 4900.5654)
Collision ability used. Setting velocity to: Vec2d(-260.2082, -5994.355)
Collision ability used. Setting velocity to: Vec2d(4859.3687, -3519.4517)
Collision ability used. Setting velocity to: Vec2d(5921.8955, -964.9612)
Collision ability used. Setting velocity to: Vec2d(5999.0625, 106.050064)


float:
Collision ability used. Setting velocity to: Vec2d(-2607.8191127413147, -5403.635764484972)
Collision ability used. Setting velocity to: Vec2d(-4210.074887668243, -4274.958413859161)
Collision ability used. Setting velocity to: Vec2d(3736.6455396544993, -4694.409452847091)
Collision ability used. Setting velocity to: Vec2d(-3128.60392549025, 5119.749747537178)
Collision ability used. Setting velocity to: Vec2d(4570.685210795385, -3887.008708996719)
Collision ability used. Setting velocity to: Vec2d(-3343.2338812904513, -4982.2472053272895)
Collision ability used. Setting velocity to: Vec2d(5037.276535690994, 3259.730832902763)
Collision ability used. Setting velocity to: Vec2d(-1060.1956527173006, -5905.589316737098)
Collision ability used. Setting velocity to: Vec2d(3460.3222902434636, 4901.6496863448165)
Collision ability used. Setting velocity to: Vec2d(5968.667863140622, 612.3756522857192)
Collision ability used. Setting velocity to: Vec2d(-3595.261236684117, 4803.550420261725)
Collision ability used. Setting velocity to: Vec2d(-3859.795778402401, -4593.688773635737)
Collision ability used. Setting velocity to: Vec2d(4854.505968835396, 3526.155384911662)
Collision ability used. Setting velocity to: Vec2d(-4961.882815409164, 3373.383898424136)
Collision ability used. Setting velocity to: Vec2d(4726.083608571183, -3696.5029047458884)
Collision ability used. Setting velocity to: Vec2d(-883.5198813009961, -5934.592877303874)
Collision ability used. Setting velocity to: Vec2d(489.0662794028498, 5980.0346298621935)
Collision ability used. Setting velocity to: Vec2d(-3946.756316157737, -4519.194018945083)
Collision ability used. Setting velocity to: Vec2d(-5895.951943185988, -1112.5424412764555)
Collision ability used. Setting velocity to: Vec2d(3123.4660464055864, -5122.885891463078)
Collision ability used. Setting velocity to: Vec2d(-5565.3182456947525, -2242.149152963979)
Collision ability used. Setting velocity to: Vec2d(4624.396015100656, 3822.951934764702)
Collision ability used. Setting velocity to: Vec2d(-5727.008580060078, 1789.238028859842)
Collision ability used. Setting velocity to: Vec2d(-5991.9346473007845, 310.99707792264553)
Collision ability used. Setting velocity to: Vec2d(-5999.829382471847, -45.247996944698976)
Collision ability used. Setting velocity to: Vec2d(-543.1521839569156, 5975.364901415046)
Collision ability used. Setting velocity to: Vec2d(5847.040565780667, 1346.1488112817622)
Collision ability used. Setting velocity to: Vec2d(5172.708284653259, -3040.2448917611127)
Collision ability used. Setting velocity to: Vec2d(3753.2538186014312, -4681.141503218396)
Collision ability used. Setting velocity to: Vec2d(-4949.223014281969, -3391.93035820338)
Collision ability used. Setting velocity to: Vec2d(-2444.2869025928735, 5479.549391858143)
Collision ability used. Setting velocity to: Vec2d(4670.442702548998, 3766.558769249035)
Collision ability used. Setting velocity to: Vec2d(-4717.129615893241, 3707.9223544813995)
Collision ability used. Setting velocity to: Vec2d(5911.405651096633, -1027.2697932786668)

