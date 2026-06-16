import re
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.utils import get_color_from_hex, platform
from kivy.clock import Clock
from kivy.animation import Animation
from scraper import cao_text_tu_web

# Thiết lập kích thước cửa sổ chuẩn điện thoại (chỉ trên desktop)
if platform != 'android':
    Window.size = (450, 780)

class ContainerWithBackground(BoxLayout):
    def __init__(self, default_hex, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.bg_color = Color(*get_color_from_hex(default_hex))
            self.bg_rect = Rectangle(size=Window.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def change_hex_color(self, hex_str):
        try:
            self.bg_color.rgba = get_color_from_hex(hex_str)
            return True
        except Exception:
            return False

class RoundedButton(Button):
    def __init__(self, bg_color_tuple, radius_val=6, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.btn_bg_color = bg_color_tuple
        self.radius_val = radius_val
        
        with self.canvas.before:
            self.canvas_color = Color(*self.btn_bg_color)
            self.canvas_rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.radius_val])
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, instance, value):
        self.canvas_rect.pos = self.pos
        self.canvas_rect.size = self.size

    def set_canvas_color(self, new_color_tuple):
        self.canvas_color.rgba = new_color_tuple

class CustomSpinnerOption(SpinnerOption):
    """Nâng cấp ô chọn con: Chiều cao co giãn động, căn lề trái phẳng, tự nhuộm màu Đỏ cam an toàn"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = '13sp'
        
        # Cấu hình lề trái phẳng lỳ chuẩn UI Book List mobile
        self.size_hint_y = None
        self.halign = 'left'
        self.valign = 'middle'
        self.padding = (16, 6) 
        
        # Ép biên ngang để khối text tự động tính dòng xuống hàng ổn định
        self.text_size = (Window.width - 64, None)
        
        with self.canvas.before:
            self.canvas_color = Color(0.15, 0.15, 0.15, 1) 
            self.canvas_rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[6])
            
            Color(0.25, 0.25, 0.25, 0.3)
            self.divider_line = Line(points=[self.x, self.y, self.x + self.width, self.y], width=1)
            
        self.bind(size=self._update_canvas, pos=self._update_canvas)
        self.bind(texture_size=self._update_dynamic_height)

    def _update_canvas(self, instance, value):
        self.text_size = (self.width - 32, None)
        if hasattr(self, 'canvas_rect') and self.canvas_rect:
            self.canvas_rect.pos = self.pos
            self.canvas_rect.size = self.size
        if hasattr(self, 'divider_line') and self.divider_line:
            self.divider_line.points = [self.x, self.y, self.x + self.width, self.y]

    def on_text(self, instance, text_value):
        """Hàm nhuộm màu bọc thép: So khớp chuỗi tiêu đề truyện nguyên bản cào từ web"""
        app = App.get_running_app()
        if app and app.root and hasattr(app.root, 'current_chapter_title_clean') and app.root.current_chapter_title_clean:
            if text_value.strip().lower() == app.root.current_chapter_title_clean.strip().lower():
                self.color = get_color_from_hex("#E74C3C") # Đỏ cam rực rỡ bừng sáng
                self.bold = True
                self.set_canvas_color((0.12, 0.12, 0.12, 1)) # Khối nền sẫm sẫm tạo tương tương tương phản
                return
                
        self.color = (0.8, 0.8, 0.8, 1)
        self.bold = False
        self.set_canvas_color((0.15, 0.15, 0.15, 1))

    def _update_dynamic_height(self, instance, value):
        """Tự động phân phối chiều cao dòng sát sao, khống chế vòng lặp vô hạn"""
        if self.texture_size[1] > 22:
            new_h = max(54, self.texture_size[1] + 12) # Ô nhiều dòng tự động nới rộng
        else:
            new_h = 38 # Ô 1 dòng tự động khóa cứng 38px phẳng lỳ gọn gàng
            
        # KHÓA XÍCH BIẾN ĐỔI: Chỉ cập nhật nếu thực sự thay đổi chiều cao để chặn đứng Layout Loop
        if self.height != new_h:
            self.height = new_h

    def set_canvas_color(self, new_color_tuple):
        # LÁ CHẮN AN TOÀN TUYỆT ĐỐI: Kiểm tra xem biến canvas đã tồn tại chưa để chống sập lúc sơ khởi
        if hasattr(self, 'canvas_color') and self.canvas_color:
            self.canvas_color.rgba = new_color_tuple

class RoundedSpinner(Spinner):
    def __init__(self, bg_color_tuple, radius_val=6, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.spinner_bg_color = bg_color_tuple
        self.radius_val = radius_val
        self.option_cls = CustomSpinnerOption
        
        with self.canvas.before:
            self.canvas_color = Color(*self.spinner_bg_color)
            self.canvas_rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.radius_val])
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, instance, value):
        self.canvas_rect.pos = self.pos
        self.canvas_rect.size = self.size

    def set_canvas_color(self, new_color_tuple):
        self.canvas_color.rgba = new_color_tuple

class RoundedInputContainer(BoxLayout):
    def __init__(self, bg_color_tuple, radius_val=6, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg_color_tuple)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[radius_val])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size

class UniversalWebReader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = (0, 0, 0, 0) 
        self.spacing = 8
        Window.clearcolor = (0.08, 0.08, 0.08, 1)

        self.COLOR_DEFAULT = (0.15, 0.15, 0.15, 1)    
        self.COLOR_ACTIVE = (0.1, 0.32, 0.46, 1)      
        self.COLOR_FETCH = (0.17, 0.24, 0.31, 1)      
        self.RADIUS_INT = 6                           

        self.current_font_size = 18
        self.current_line_height = 1.4      
        self.current_para_spacing = 15     
        self.text_color_hex = "#202020" 
        self.bg_color_hex = "#F4ECD8"   
        self.paragraphs_data = ["Welcome to Universal Web Reader. Type or paste your link above to start reading..."]
        self.prev_chapter_url = ""
        self.next_chapter_url = ""
        self.chapters_mapping = {} 
        self.current_chapter_title_clean = "" 

        # ĐỊNH NGHĨA BIẾN KIỂM SOÁT ĐỒ HỌA HOẠT ẢNH ẨN/HIỆN
        self.header_state = "shown"      
        self.last_scroll_y = 1.0         
        self.is_loading_page = False     

        # Hộp chứa tổng thể Header (Chứa 2 hàng link + chọn chương)
        self.header_bar = BoxLayout(orientation='vertical', size_hint_y=None, height=98, spacing=8, padding=(0, 10, 0, 0))

        # Hàng 1: Ô nhập link + Nút Fetch + SET
        self.top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=42, spacing=5)
        self.top_bar.padding = (10, 0, 10, 0)
        self.input_wrapper = RoundedInputContainer(bg_color_tuple=(0.15, 0.15, 0.15, 1), radius_val=self.RADIUS_INT)
        self.url_input = TextInput(
            text='https://khotruyenchu.fun/chuong-346-thanh-kiem-tam-pham-thien-vi/', 
            multiline=False, hint_text='Paste web link here...',
            foreground_color=(0.9, 0.9, 0.9, 1), cursor_color=(1, 1, 1, 1),
            padding=(8, 11, 8, 8), background_normal='', background_active='', background_color=(0, 0, 0, 0)
        )
        self.input_wrapper.add_widget(self.url_input)
        self.btn_fetch = RoundedButton(bg_color_tuple=self.COLOR_FETCH, radius_val=self.RADIUS_INT, text='Fetch', size_hint_x=0.18)
        self.btn_fetch.bind(on_press=lambda inst: self.load_new_page(self.url_input.text.strip()))
        self.btn_settings_toggle = RoundedButton(bg_color_tuple=self.COLOR_DEFAULT, radius_val=self.RADIUS_INT, text='SET', font_size='13sp', size_hint_x=0.14)
        self.btn_settings_toggle.bind(on_press=self.toggle_all_settings_panel)
        self.top_bar.add_widget(self.input_wrapper)
        self.top_bar.add_widget(self.btn_fetch)
        self.top_bar.add_widget(self.btn_settings_toggle)

        # Hàng 2: Nút di chuyển điều hướng chương truyện
        self.nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=5)
        self.nav_bar.padding = (10, 0, 10, 0)
        self.btn_prev_chap = RoundedButton(bg_color_tuple=self.COLOR_DEFAULT, radius_val=self.RADIUS_INT, text='[<] Prev', size_hint_x=0.22, disabled=True)
        self.btn_prev_chap.bind(on_press=self.go_prev_chapter)
        self.spinner_toc = RoundedSpinner(bg_color_tuple=self.COLOR_DEFAULT, radius_val=self.RADIUS_INT, text='Table of Contents', values=(), size_hint_x=0.56)
        self.spinner_toc.bind(text=self.on_toc_chapter_selected)
        self.spinner_toc.bind(is_open=self.on_spinner_dropdown_state_changed)
        self.btn_next_chap = RoundedButton(bg_color_tuple=self.COLOR_DEFAULT, radius_val=self.RADIUS_INT, text='Next [>]', size_hint_x=0.22, disabled=True)
        self.btn_next_chap.bind(on_press=self.go_next_chapter)
        self.nav_bar.add_widget(self.btn_prev_chap)
        self.nav_bar.add_widget(self.spinner_toc)
        self.nav_bar.add_widget(self.btn_next_chap)

        # Nạp cả 2 hàng vào Header tổng
        self.header_bar.add_widget(self.top_bar)
        self.header_bar.add_widget(self.nav_bar)
        self.add_widget(self.header_bar)

        # Bảng cài đặt cỡ chữ nâng cao
        self.master_settings_layout = GridLayout(cols=2, rows=5, size_hint_y=None, height=0, opacity=0, spacing=6, padding=(10, 4, 10, 4))
        self.lbl_slider_size = Label(text=f"Font Size: {self.current_font_size} sp", font_size='13sp', size_hint_x=0.25)
        self.font_slider = Slider(min=12, max=45, value=18, step=1)
        self.font_slider.bind(value=self.on_font_slider_changed)
        self.master_settings_layout.add_widget(self.lbl_slider_size)
        self.master_settings_layout.add_widget(self.font_slider)
        
        self.lbl_slider_lh = Label(text=f"Line Height: {self.current_line_height}", font_size='13sp')
        self.lh_slider = Slider(min=1.0, max=2.5, value=1.4, step=0.1)
        self.lh_slider.bind(value=self.on_lh_slider_changed)
        self.master_settings_layout.add_widget(self.lbl_slider_lh)
        self.master_settings_layout.add_widget(self.lh_slider)
        
        self.lbl_slider_ps = Label(text=f"Para Space: {self.current_para_spacing}px", font_size='13sp')
        self.ps_slider = Slider(min=0, max=40, value=15, step=1)
        self.ps_slider.bind(value=self.on_ps_slider_changed)
        self.master_settings_layout.add_widget(self.lbl_slider_ps)
        self.master_settings_layout.add_widget(self.ps_slider)
        
        self.lbl_preset_title = Label(text="Presets:", font_size='13sp')
        self.preset_colors_layout = BoxLayout(orientation='horizontal', spacing=4)
        presets = [("Paper", "#F4ECD8", "#151515"), ("White", "#FFFFFF", "#000000"), ("Dark", "#1E1E1E", "#E0E0E0"), ("Sepia", "#EFE6D5", "#251F15")]
        for name, bg_hex, text_hex in presets:
            btn_preset = RoundedButton(bg_color_tuple=get_color_from_hex(bg_hex), radius_val=self.RADIUS_INT, text=name, font_size='11sp')
            btn_preset.bg_hex = bg_hex; btn_preset.text_hex = text_hex
            btn_preset.bind(on_press=self.on_preset_color_clicked)
            self.preset_colors_layout.add_widget(btn_preset)
        self.master_settings_layout.add_widget(self.lbl_preset_title)
        self.master_settings_layout.add_widget(self.preset_colors_layout)
        
        self.hex_container_left = BoxLayout(orientation='horizontal', spacing=4)
        self.lbl_bg_hex = Label(text="Background:", size_hint_x=0.45, font_size='12sp')
        self.wrapper_bg_input = RoundedInputContainer(bg_color_tuple=(0.15, 0.15, 0.15, 1), radius_val=self.RADIUS_INT)
        self.bg_hex_input = TextInput(text='#F4ECD8', multiline=False, foreground_color=(1, 1, 1, 1), padding=(6, 10, 6, 8), background_normal='', background_active='', background_color=(0,0,0,0))
        self.bg_hex_input.bind(text=self.on_bg_hex_changed)
        self.wrapper_bg_input.add_widget(self.bg_hex_input)
        self.hex_container_left.add_widget(self.lbl_bg_hex)
        self.hex_container_left.add_widget(self.wrapper_bg_input)
        
        self.hex_container_right = BoxLayout(orientation='horizontal', spacing=4)
        self.lbl_txt_hex = Label(text="Text Color:", size_hint_x=0.45, font_size='12sp')
        self.wrapper_txt_input = RoundedInputContainer(bg_color_tuple=(0.15, 0.15, 0.15, 1), radius_val=self.RADIUS_INT)
        self.text_hex_input = TextInput(text='#202020', multiline=False, foreground_color=(1, 1, 1, 1), padding=(6, 10, 6, 8), background_normal='', background_active='', background_color=(0,0,0,0))
        self.text_hex_input.bind(text=self.on_text_hex_changed)
        self.wrapper_txt_input.add_widget(self.text_hex_input)
        self.hex_container_right.add_widget(self.lbl_txt_hex)
        self.hex_container_right.add_widget(self.wrapper_txt_input)
        
        self.master_settings_layout.add_widget(self.hex_container_left)
        self.master_settings_layout.add_widget(self.hex_container_right)
        self.add_widget(self.master_settings_layout)

        # Không gian đọc truyện chính
        self.reading_container = ContainerWithBackground(default_hex='#F4ECD8', size_hint_y=1.0)
        self.scroll_view = ScrollView(scroll_type=['content'], bar_width=0)
        self.scroll_view.bind(scroll_y=self.on_scroll_y_changed)
        
        self.text_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=self.current_para_spacing, padding=(20, 15, 20, 15))
        self.text_layout.bind(minimum_height=self.text_layout.setter('height'))
        
        self.scroll_view.add_widget(self.text_layout)
        self.reading_container.add_widget(self.scroll_view)
        self.add_widget(self.reading_container)
        
        self.build_scrolling_content()

    def on_scroll_y_changed(self, instance, value):
        """Hàm lọc và định hướng trườn hoạt ảnh mượt mà, vá lỗi _dropdown an toàn"""
        has_dropdown = hasattr(self.spinner_toc, '_dropdown') and self.spinner_toc._dropdown
        if self.is_loading_page or (has_dropdown and self.spinner_toc._dropdown.parent):
            self.last_scroll_y = value
            return
            
        if value < 0.0 or value > 1.0:
            return
            
        diff = value - self.last_scroll_y
        self.last_scroll_y = value
        
        if abs(diff) < 0.0015:
            return
            
        if diff < 0 and self.header_state == "shown":
            self.header_state = "hidden"
            if self.master_settings_layout.height > 0:
                self.master_settings_layout.height = 0
                self.master_settings_layout.opacity = 0
                self.btn_settings_toggle.set_canvas_color(self.COLOR_DEFAULT)
                
            anim = Animation(height=0, opacity=0, duration=0.22, t='out_cubic')
            anim.start(self.header_bar)
            
        elif diff > 0 and self.header_state == "hidden":
            self.header_state = "shown"
            anim = Animation(height=98, opacity=1, duration=0.22, t='out_cubic')
            anim.start(self.header_bar)

    def build_scrolling_content(self):
        self.text_layout.clear_widgets()
        self.text_layout.spacing = self.current_para_spacing
        
        if not self.paragraphs_data: return
        max_chars_per_label = max(400, int(120000 / (self.current_font_size ** 1.5)))
        for paragraph in self.paragraphs_data:
            if len(paragraph) < max_chars_per_label:
                self.add_text_label_block(paragraph)
            else:
                words = paragraph.split(' ')
                sub_block = ""
                for word in words:
                    if len(sub_block) + len(word) + 1 < max_chars_per_label:
                        sub_block += word + " "
                    else:
                        self.add_text_label_block(sub_block.strip())
                        sub_block = word + " "
                if sub_block: self.add_text_label_block(sub_block.strip())

    def add_text_label_block(self, text_content):
        lbl = Label(
            text=text_content, font_size=f"{self.current_font_size}sp",
            line_height=self.current_line_height,
            color=get_color_from_hex(self.text_color_hex), halign='justify', valign='top',
            size_hint_y=None, text_size=(Window.width - 40, None)
        )
        lbl.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        self.text_layout.add_widget(lbl)

    def load_new_page(self, url):

        if not url or "http" not in url:
            self.paragraphs_data = ["Please enter a valid website link!"]
            self.build_scrolling_content()
            return
            
        self.is_loading_page = True
        self.url_input.text = url
        self.paragraphs_data = ["Loading chapter data, please wait..."]
        self.build_scrolling_content()
        
        # Chạy network call trong thread riêng để tránh đóng băng UI (ANR)
        thread = threading.Thread(target=self._fetch_in_background, args=(url,))
        thread.daemon = True
        thread.start()

    def _fetch_in_background(self, url):
        """Chạy trên background thread — KHÔNG được thao tác UI ở đây"""
        try:
            web_data = cao_text_tu_web(url)
        except Exception as e:
            web_data = {
                "paragraphs": [f"System error: {str(e)}"],
                "prev_url": "", "next_url": "", "chapters": []
            }
        # Quay về main thread để cập nhật UI an toàn
        Clock.schedule_once(lambda dt: self._on_fetch_complete(url, web_data), 0)

    def _on_fetch_complete(self, url, web_data):
        """Callback chạy trên main thread sau khi fetch xong"""
        self.paragraphs_data = web_data["paragraphs"]
        self.scroll_view.scroll_y = 1.0 
        self.last_scroll_y = 1.0
        
        if self.header_state == "hidden":
            self.header_state = "shown"
            self.header_bar.height = 98
            self.header_bar.opacity = 1
        
        self.prev_chapter_url = web_data["prev_url"]
        self.next_chapter_url = web_data["next_url"]
        self.btn_prev_chap.disabled = not bool(self.prev_chapter_url)
        self.btn_next_chap.disabled = not bool(self.next_chapter_url)
        
        self.btn_prev_chap.set_canvas_color(self.COLOR_DEFAULT if self.prev_chapter_url else (0.1, 0.1, 0.1, 1))
        self.btn_next_chap.set_canvas_color(self.COLOR_DEFAULT if self.next_chapter_url else (0.1, 0.1, 0.1, 1))
        
        danh_sach_tho = web_data["chapters"]
        num_match_current = re.search(r'chuong-(\d+)', url.lower())
        current_num = int(num_match_current.group(1)) if num_match_current else None
        
        if current_num is not None and danh_sach_tho:
            co_san_chương_hien_tai = any(d["num"] == current_num for d in danh_sach_tho)
            
            if not co_san_chương_hien_tai:
                ten_chuong_tu_che = f"Chương {current_num}: Hiện tại"
                if self.paragraphs_data and "Chương" in self.paragraphs_data[0]:
                    ten_chuong_tu_che = self.paragraphs_data[0].split('\n')[0][:50]
                danh_sach_tho.append({"title": ten_chuong_tu_che, "url": url, "num": current_num})
                danh_sach_tho.sort(key=lambda x: x["num"])
                
            index_hien_tai = -1
            for idx, item in enumerate(danh_sach_tho):
                if item["num"] == current_num:
                    index_hien_tai = idx
                    break
                    
            start_idx = max(0, index_hien_tai - 5)
            end_idx = min(len(danh_sach_tho), index_hien_tai + 6)
            danh_sach_rut_gon = danh_sach_tho[start_idx:end_idx]
            
            self.chapters_mapping = {}
            spinner_values = []
            
            for item in danh_sach_rut_gon:
                title = item["title"]
                link = item["url"]
                
                if item["num"] == current_num:
                    self.current_chapter_title_clean = title
                    
                self.chapters_mapping[title] = link
                spinner_values.append(title)
                
            self.spinner_toc.values = spinner_values
        else:
            self.spinner_toc.values = ["Current Chapter"]
            self.chapters_mapping = {"Current Chapter": url}
            self.current_chapter_title_clean = "Current Chapter"
            
        self.spinner_toc.text = 'Table of Contents'
        self.build_scrolling_content()
        self.is_loading_page = False

    def force_refresh_dropdown_colors(self, spinner_instance):
        if hasattr(spinner_instance, '_dropdown') and spinner_instance._dropdown:
            container = spinner_instance._dropdown.container
            for child in container.children:
                if isinstance(child, CustomSpinnerOption):
                    child.on_text(child, child.text)

    def toggle_all_settings_panel(self, instance):
        if self.master_settings_layout.height == 0:
            self.master_settings_layout.height = 185
            self.master_settings_layout.opacity = 1
            instance.set_canvas_color(self.COLOR_ACTIVE) 
        else:
            self.master_settings_layout.height = 0
            self.master_settings_layout.opacity = 0
            instance.set_canvas_color(self.COLOR_DEFAULT)

    def on_spinner_dropdown_state_changed(self, instance, is_open):
        if is_open:
            instance.set_canvas_color(self.COLOR_ACTIVE) 
            Clock.schedule_once(lambda dt: self.force_refresh_dropdown_colors(instance), 0.02)
        else:
            instance.set_canvas_color(self.COLOR_DEFAULT) 

    def update_text_styles(self):
        """Cập nhật style cho các Label hiện có mà không tạo lại widget — tối ưu hiệu năng"""
        self.text_layout.spacing = self.current_para_spacing
        try:
            t_color = get_color_from_hex(self.text_color_hex)
        except Exception:
            t_color = (0, 0, 0, 1)
        for child in self.text_layout.children:
            child.font_size = f"{self.current_font_size}sp"
            child.line_height = self.current_line_height
            child.color = t_color

    def on_font_slider_changed(self, instance, value):
        self.current_font_size = int(value)
        self.lbl_slider_size.text = f"Font Size: {self.current_font_size} sp"
        self.update_text_styles()

    def on_lh_slider_changed(self, instance, value):
        self.current_line_height = round(value, 1)
        self.lbl_slider_lh.text = f"Line Height: {self.current_line_height}"
        self.update_text_styles()

    def on_ps_slider_changed(self, instance, value):
        self.current_para_spacing = int(value)
        self.lbl_slider_ps.text = f"Para Space: {self.current_para_spacing}px"
        self.update_text_styles()

    def on_preset_color_clicked(self, instance):
        self.bg_color_hex = instance.bg_hex; self.text_color_hex = instance.text_hex
        self.reading_container.change_hex_color(self.bg_color_hex)
        self.bg_hex_input.text = self.bg_color_hex; self.text_hex_input.text = self.text_color_hex
        try:
            t_color = get_color_from_hex(self.text_color_hex)
            for child in self.text_layout.children: child.color = t_color
        except Exception: pass

    def on_bg_hex_changed(self, instance, text_nhap):
        hex_str = text_nhap.strip()
        if hex_str and not hex_str.startswith('#'): hex_str = '#' + hex_str
        if len(hex_str) in (4, 7):
            if self.reading_container.change_hex_color(hex_str): self.bg_color_hex = hex_str

    def on_text_hex_changed(self, instance, text_nhap):
        hex_str = text_nhap.strip()
        if hex_str and not hex_str.startswith('#'): hex_str = '#' + hex_str
        if len(hex_str) in (4, 7):
            self.text_color_hex = hex_str
            try:
                t_color = get_color_from_hex(self.text_color_hex)
                for child in self.text_layout.children: child.color = t_color
            except Exception: pass

    def go_prev_chapter(self, instance):
        if self.prev_chapter_url: self.load_new_page(self.prev_chapter_url)

    def go_next_chapter(self, instance):
        if self.next_chapter_url: self.load_new_page(self.next_chapter_url)

    def on_toc_chapter_selected(self, spinner, text_selected):
        if text_selected == 'Table of Contents': return
        target_url = self.chapters_mapping.get(text_selected)
        self.spinner_toc.text = 'Table of Contents'
        if target_url: self.load_new_page(target_url)

class MainApp(App):
    def build(self):
        self.title = 'Universal Web Reader'
        return UniversalWebReader()

if __name__ == '__main__':
    MainApp().run()