import pymunk
from shapes.shape import Shape

class Circle(Shape):
    
    def __init__(
                self, 
                position: tuple = (300, 100), 
                velocity: tuple = (0, 0), 
                body = None, 

                shape_radio: int = 20, 
                shape_mass: int = 1, 
                shape_friction: int = 0.1, 
            ):
        """
        position: tuple = (300, 100) # 设置身体的位置

        velocity: tuple = (0, 0) # 賦予物體向右的初速度

        body:
            pymunk.Body(shape_type)

            shape_type:
                pymunk.Body.STATIC, pymunk.Body.DYNAMIC, pymunk.Body.KINEMATIC

        shape: 
            pymunk.Circle, pymunk.Segment
        
        shape_mass: int = 1 # 设置 shape 的质量为1

        shape_friction: int = 0.1 # 设置 shape 的摩擦係數为1
        """

        super().__init__(position, velocity, body, )
        self.shape = pymunk.Circle(self.body, shape_radio) # 创建一个半径为20像素的圆形的形状，并绑定其“身体”
        self.shape.mass = shape_mass # 设置 shape 的质量为1
        self.shape.friction = shape_friction # 设置 shape 的摩擦係數为1
        pass
