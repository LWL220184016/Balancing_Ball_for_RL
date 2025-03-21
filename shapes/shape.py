import pymunk

class Shape:
    
    def __init__(
                self, 
                position: tuple = (300, 100), # 设置身体的位置
                velocity: tuple = (0, 0), # 賦予物體向 XY 的初速度
                body = None, 
                shape = None,
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
        """
        
        self.body = body
        self.default_position = position 
        self.default_velocity = velocity 
        self.body.position = position 
        self.body.velocity = velocity 

        self.shape = shape
        
    def reset(self):
        self.body.position = self.default_position 
        self.body.velocity = self.default_velocity 

