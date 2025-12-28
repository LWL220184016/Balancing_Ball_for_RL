import moderngl
import numpy as np
import pygame
import sys

class ModernGLRenderer:
    def __init__(self, width, height, obs_width=160, obs_height=160, headless=False):
        self.width = width
        self.height = height

        self.obs_width = obs_width
        self.obs_height = obs_height
        self.headless = headless
        
        if self.headless:
            if sys.platform.startswith('linux'):
                # Linux 伺服器使用 EGL (最高效能)
                try:
                    self.ctx = moderngl.create_context(standalone=True, backend='egl')
                except Exception as e:
                    print(f"EGL context failed on Linux, falling back to default: {e}")
                    self.ctx = moderngl.create_context(standalone=True)
            else:
                # Windows 不支持 'egl'
                self.ctx = moderngl.create_context(standalone=True)
            # 用於 RL 訓練，縮小圖片增加效能
            self.fbo_render = self.ctx.simple_framebuffer((obs_width, obs_height), components=3)
        else:
            self.ctx = moderngl.create_context(standalone=False)
            self.fbo_render = self.ctx.screen
            
            # 初始化紋理渲染器 (僅在非 headless 或需要錄影時需要 UI)
            self._init_texture_renderer()
            self.ui_texture = self.ctx.texture((width, height), 4)

        self.fbo_render.use()
        self.ctx.enable(moderngl.BLEND) 
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # 投影矩陣
        self.prog_matrix = self.get_ortho_matrix(0, width, height, 0)

        # 初始化 Shader
        self.shader = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                uniform mat4 proj;
                void main() {
                    gl_Position = proj * vec4(in_vert, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                uniform vec4 color;
                out vec4 f_color;
                void main() {
                    f_color = color;
                }
            ''',
        )
        self.shader['proj'].write(self.prog_matrix)

        # 預留緩衝區 (幾何用)
        # 如果顯存允許，可以開大一點避免頻繁重新分配
        self.vbo = self.ctx.buffer(reserve=16 * 1024) 
        self.vao = self.ctx.vertex_array(self.shader, [(self.vbo, '2f', 'in_vert')])
        
    def get_ortho_matrix(self, left, right, bottom, top):
        rml, tmb = right - left, top - bottom
        a = 2.0 / rml
        b = 2.0 / tmb
        c = -(right + left) / rml
        d = -(top + bottom) / tmb
        return np.array([a, 0, 0, 0,  0, b, 0, 0,  0, 0, -1, 0,  c, d, 0, 1], dtype='f4')

    def clear(self, color):
        # 無論是螢幕還是 FBO，調用 use() 後 clear 都會作用在當前綁定的 Framebuffer
        self.fbo_render.clear(color[0]/255, color[1]/255, color[2]/255)

    def read_pixels(self):
        """
        這一步全在 GPU 完成：
        將高清畫面 (fbo_render) 縮小並複製到 低清 FBO (fbo_obs)
        """
        raw_data = self.fbo_render.read(components=3)
        img = np.frombuffer(raw_data, dtype=np.uint8).reshape((self.obs_width, self.obs_height, 3))
        return np.flipud(img)


    def draw_polygon(self, vertices, color, outline_color=(255,255,255), outline_width=2):
        if len(color) == 3: color = (*color, 255)
        gl_color = tuple(c/255 for c in color)
        
        data = np.array(vertices, dtype='f4').flatten()
        self.vbo.write(data)
        
        self.shader['color'].write(np.array(gl_color, dtype='f4'))
        self.vao.render(moderngl.TRIANGLE_FAN, vertices=len(vertices))

        if outline_width > 0:
            gl_outline = tuple(c/255 for c in outline_color + (255,))
            self.shader['color'].write(np.array(gl_outline, dtype='f4'))
            self.ctx.line_width = float(outline_width)
            self.vao.render(moderngl.LINE_LOOP, vertices=len(vertices))

    def draw_circle(self, position, radius, color, outline_color=(255,255,255)):
        num_segments = 32
        theta = np.linspace(0, 2*np.pi, num_segments, endpoint=False)
        x = position[0] + radius * np.cos(theta)
        y = position[1] + radius * np.sin(theta)
        vertices = np.column_stack([x, y])
        self.draw_polygon(vertices, color, outline_color)

    def _init_texture_renderer(self):
        self.tex_shader = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D texture0;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    f_color = texture(texture0, v_texcoord);
                }
            '''
        )
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        self.quad_buffer = self.ctx.buffer(vertices.tobytes())
        self.quad_vao = self.ctx.vertex_array(
            self.tex_shader, 
            [(self.quad_buffer, '2f 2f', 'in_vert', 'in_texcoord')]
        )

    def draw_texture(self, surface):
        if surface.get_size() != self.ui_texture.size:
             self.ui_texture = self.ctx.texture(surface.get_size(), 4)
        texture_data = pygame.image.tostring(surface, "RGBA", True)
        self.ui_texture.write(texture_data)
        self.ui_texture.use(0)
        self.ctx.enable(moderngl.BLEND) 
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)