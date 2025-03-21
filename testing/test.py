import pymunk

WINDOW_X = 1000
WINDOW_Y = 600

space = pymunk.Space() # 创建一个pymunk物理空间
space.gravity = (0, 1000) # 添加重力
space.damping = 0.6 # 空氣阻力, 物體每秒損失 40% 的速度

dynamic_body = pymunk.Body() # 動態身體, DYNAMIC 是預設的
dynamic_body.position = (300, 400) # 设置身体的位置
dynamic_body.velocity = (400, 0) # 賦予物體向右的初速度
static_body = pymunk.Body(pymunk.Body.STATIC)

shape1 = pymunk.Segment(space.static_body, (5, WINDOW_Y-100), (WINDOW_X-5, WINDOW_Y-100), 1.0)
shape1.mass = 1 # 设置 shape1 的质量为1
shape1.friction = 1
shape2 = pymunk.Circle(dynamic_body, 20) # 创建一个半径为20像素的圆形的形状，并绑定其“身体”
shape2.mass = 1 # 设置 shape2 的质量为1

space.add(shape1, dynamic_body, shape2) # 将身体和形状加入 pymunk 空间

def func(): 
    dynamic_body.apply_force_at_local_point((10, 0), (0, 0)) # 賦予物體向右的加速度

if __name__ == "__main__":
    import util
    util.run(space, func, (WINDOW_X, WINDOW_Y)) # 这里调用了util.py用于显示pymunk的运行结果
