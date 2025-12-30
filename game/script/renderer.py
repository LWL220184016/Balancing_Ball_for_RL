import moderngl
import numpy as np
import sys
import pygame

class ModernGLRenderer:
    def __init__(self, width, height, obs_width=160, obs_height=160, headless=False):
        self.width = width
        self.height = height
        self.obs_width = obs_width
        self.obs_height = obs_height
        self.headless = headless
        
        if headless:
            if sys.platform.startswith('linux'):
                try:
                    self.ctx = moderngl.create_context(standalone=True, backend='egl')
                except:
                    self.ctx = moderngl.create_context(standalone=True)
            else:
                self.ctx = moderngl.create_context(standalone=True)
            # 使用單通道 (Luminance) 緩衝區，節省 GPU 記憶體和 read_pixels 頻寬
            self.fbo_render = self.ctx.simple_framebuffer((obs_width, obs_height), components=1)
            self._build_ctx_program_gray()
        else:
            self.ctx = moderngl.create_context(standalone=False)
            self.fbo_render = self.ctx.screen
            self._init_texture_renderer()
            self.ui_texture = self.ctx.texture((width, height), 4)
            self._build_ctx_program_rgb()

        # 啟用混合模式
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # 預計算投影矩陣
        self.proj_matrix = self.get_ortho_matrix(0, width, height, 0)
        
        # 初始化兩個專用的批量渲染器 
        self._init_circle_renderer()
        self._init_poly_renderer()

    def get_ortho_matrix(self, left, right, bottom, top):
        rml, tmb = right - left, top - bottom
        a, b = 2.0 / rml, 2.0 / tmb
        c, d = -(right + left) / rml, -(top + bottom) / tmb
        return np.array([a, 0, 0, 0,  0, b, 0, 0,  0, 0, -1, 0,  c, d, 0, 1], dtype='f4')

    # ==========================================
    # ⚡️ 圓形渲染器 (Instancing + SDF)
    # ==========================================
    def _init_circle_renderer(self):
        """
        使用實例化渲染畫圓。
        我們不畫32邊形，而是畫一個正方形，然後在 Shader 裡把多餘的像素丟掉變成圓。
        """
        self.circle_prog['proj'].write(self.proj_matrix)
        
        # 基礎幾何體：一個單位正方形 (2x2)
        quad_verts = np.array([
            -1.0, -1.0,  1.0, -1.0,  -1.0, 1.0,  1.0, 1.0
        ], dtype='f4')
        self.vbo_circle_quad = self.ctx.buffer(quad_verts.tobytes())
        
        # 實例數據緩衝區 (預分配大一點，比如支持 2000 個圓)
        # 格式: [x, y, radius, r, g, b] -> 6 floats
        self.max_circles = 2000
        self.vbo_circle_instance = self.ctx.buffer(reserve=self.max_circles * 6 * 4)
        
        # VAO 設置
        self.vao_circle = self.ctx.vertex_array(
            self.circle_prog,
            [
                (self.vbo_circle_quad, '2f', 'in_vert'),
                (self.vbo_circle_instance, '2f 1f 3f/i', 'in_pos', 'in_radius', 'in_color')
            ]
        )

    def render_circles(self, circle_data_list):
        """
        circle_data_list: numpy array or list of [x, y, radius, r, g, b]
        """
        if not circle_data_list:
            return
            
        data = np.array(circle_data_list, dtype='f4')
        count = len(data)
        
        # 如果數據超過緩衝區大小，這裡需要重新分配 (簡化起見假設不超過)
        self.vbo_circle_instance.write(data.tobytes())
        self.vao_circle.render(moderngl.TRIANGLE_STRIP, instances=count)

    # ==========================================
    # ⚡️ 多邊形渲染器 (Batching)
    # ==========================================
    def _init_poly_renderer(self):
        self.poly_prog['proj'].write(self.proj_matrix)
        
        # 預分配大緩衝區 (支持 10000 個頂點)
        # 格式: [x, y, r, g, b, a]
        self.max_poly_verts = 10000
        self.vbo_poly = self.ctx.buffer(reserve=self.max_poly_verts * 6 * 4)
        self.vao_poly = self.ctx.vertex_array(
            self.poly_prog,
            [(self.vbo_poly, '2f 4f', 'in_pos', 'in_color')]
        )

    def render_polygons(self, vertices_data, vertex_count):
        """
        vertices_data: 扁平化的 bytes 或 numpy array
        vertex_count: 頂點總數
        """
        if vertex_count == 0:
            return
        self.vbo_poly.write(vertices_data)
        self.vao_poly.render(moderngl.TRIANGLES, vertices=vertex_count)

    def clear(self, color=(0, 0, 0)):
        self.fbo_render.use()
        self.fbo_render.clear(color[0]/255, color[1]/255, color[2]/255)

    def read_pixels(self):
        raw = self.fbo_render.read(components=1, dtype='f1') # 'f1' 對應 uint8
        img = np.frombuffer(raw, dtype=np.uint8).reshape((self.obs_height, self.obs_width))
        
        # RL 通常需要 (H, W, 1) 的形狀
        # np.flipud 會產生一個視圖或副本，如果 RL 框架支持，可以考慮在 Shader 裡直接翻轉 Y 以節省此步驟
        return np.flipud(img)[:, :, np.newaxis]

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


    def _build_ctx_program_rgb(self):
        
        self.circle_prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;      // 正方形的基礎頂點 (-1~1)
                in vec2 in_pos;       // 圓心位置 (Instance Data)
                in float in_radius;   // 半徑 (Instance Data)
                in vec3 in_color;     // 顏色 (Instance Data)
                
                uniform mat4 proj;
                
                out vec2 v_uv;        // 用於計算圓形的 UV
                out vec3 v_color;
                
                void main() {
                    v_uv = in_vert;
                    v_color = in_color;
                    // 將單位正方形縮放並移動到圓心
                    vec2 pos = in_pos + (in_vert * in_radius);
                    gl_Position = proj * vec4(pos, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_uv;
                in vec3 v_color;
                out vec4 f_color;
                
                void main() {
                    // 計算當前像素距離中心的距離 (SDF)
                    float dist = length(v_uv);
                    // 如果距離大於1 (在圓外)，丟棄像素；否則平滑邊緣 (Anti-aliasing)
                    float delta = fwidth(dist);
                    float alpha = 1.0 - smoothstep(1.0 - delta, 1.0, dist);
                    
                    if (alpha <= 0.0) discard;
                    
                    f_color = vec4(v_color, alpha);
                }
            '''
        )

        self.poly_prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_pos;
                in vec4 in_color;
                uniform mat4 proj;
                out vec4 v_color;
                void main() {
                    gl_Position = proj * vec4(in_pos, 0.0, 1.0);
                    v_color = in_color;
                }
            ''',
            fragment_shader='''
                #version 330
                in vec4 v_color;
                out vec4 f_color;
                void main() {
                    f_color = v_color;
                }
            '''
        )

    def _build_ctx_program_gray(self):

        self.circle_prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;      // 正方形的基礎頂點 (-1~1)
                in vec2 in_pos;       // 圓心位置 (Instance Data)
                in float in_radius;   // 半徑 (Instance Data)
                in vec3 in_color;     // 顏色 (Instance Data)
                
                uniform mat4 proj;
                
                out vec2 v_uv;        // 用於計算圓形的 UV
                out vec3 v_color;
                
                void main() {
                    v_uv = in_vert;
                    v_color = in_color;
                    // 將單位正方形縮放並移動到圓心
                    vec2 pos = in_pos + (in_vert * in_radius);
                    gl_Position = proj * vec4(pos, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_uv;
                in vec3 v_color;
                out vec4 f_color;
                
                void main() {
                    // 計算當前像素距離中心的距離 (SDF)
                    float dist = length(v_uv);
                    // 如果距離大於1 (在圓外)，丟棄像素；否則平滑邊緣 (Anti-aliasing)
                    float delta = fwidth(dist);
                    float alpha = 1.0 - smoothstep(1.0 - delta, 1.0, dist);
                    
                    if (alpha <= 0.0) discard;
                    
                    // 標準灰度公式 (Luminance): 0.299R + 0.587G + 0.114B
                    float gray = dot(v_color, vec3(0.299, 0.587, 0.114));
                    
                    // 寫入 vec4。因為 FBO components=1，它會取第一個值 (gray)
                    f_color = vec4(gray, gray, gray, alpha);
                }
            '''
        )

        self.poly_prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_pos;
                in vec4 in_color;
                uniform mat4 proj;
                out vec4 v_color;
                void main() {
                    gl_Position = proj * vec4(in_pos, 0.0, 1.0);
                    v_color = in_color;
                }
            ''',
            fragment_shader='''
                #version 330
                in vec4 v_color;
                out vec4 f_color;
                void main() {
                    // 將傳入的 RGB 轉換為灰度，保留 Alpha 用於混合
                    float gray = dot(v_color.rgb, vec3(0.299, 0.587, 0.114));
                    f_color = vec4(gray, gray, gray, v_color.a);
                }
            '''
        )