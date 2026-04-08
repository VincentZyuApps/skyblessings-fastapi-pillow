"""
图片渲染模块
负责生成祈福签图片
"""

import random
import io
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from draw_data import (
    DRAW_ITEMS,
    DrawItem,
    BACKGROUND_IMAGE_MAP,
    TEXT_IMAGE_MAP,
    extract_color_from_name
)


@dataclass
class BlessingResult:
    """抽签结果"""
    background_image: str = ""  # 背景装饰图文件名
    background_id: str = ""     # 背景编号，如 backgroundimg0
    text_image: str = ""        # 签文图片文件名
    fortune_level: str = ""     # 吉祥程度，如 大吉/中吉
    dordas: str = ""            # 结缘物
    dordas_color: str = ""      # 缘彩名称
    color_hex: str = ""         # 颜色十六进制
    blessing: str = ""          # 祝福语
    entry: str = ""             # 词条


class BlessingRenderer:
    """祈福签渲染器"""
    
    def __init__(self, config: dict):
        """
        初始化渲染器
        
        Args:
            config: 配置字典，包含 image 和 assets 配置
        """
        self.config = config
        self.width = config['image']['width']
        self.height = config['image']['height']
        self.font_size = config['image']['font_size']
        self.assets_dir = Path(config['image']['assets_dir'])
        
        # 缓存字体（字典，键为字体大小）
        self.font_cache: dict[int, ImageFont.FreeTypeFont] = {}
    
    def _load_font(self, size: Optional[int] = None) -> ImageFont.FreeTypeFont:
        """加载字体"""
        font_size = size if size is not None else self.font_size
        
        if font_size not in self.font_cache:
            font_path = self.assets_dir / "font" / "LXGWWenKaiMono-Medium.ttf"
            try:
                self.font_cache[font_size] = ImageFont.truetype(str(font_path), font_size)
            except Exception as e:
                print(f"警告：加载字体失败 {e}，使用默认字体")
                self.font_cache[font_size] = ImageFont.load_default()
        return self.font_cache[font_size]
    
    def _get_children(self, parent_id: str) -> list[DrawItem]:
        """获取指定父节点的所有子项"""
        return [item for item in DRAW_ITEMS if item.parent_id == parent_id]
    
    def _draw_random_item(self, items: list[DrawItem], rng: random.Random = None) -> DrawItem:
        """根据权重随机选择一个项"""
        if not items:
            raise ValueError("没有可选项")
        if rng is None:
            rng = random
        total_weight = sum(item.weight for item in items)
        rand_num = rng.randint(1, total_weight)

        cumulative = 0
        for item in items:
            cumulative += item.weight
            if rand_num <= cumulative:
                return item

        return items[-1]

    def _draw_sub_items(self, parent_id: str, result: BlessingResult, rng: random.Random = None):
        """递归抽取子项"""
        children = self._get_children(parent_id)
        if not children:
            return

        selected = self._draw_random_item(children, rng)
        
        # 根据类型填充结果
        if selected.remark == "dordas":
            result.dordas = selected.name
        elif selected.remark == "dordascolor":
            result.dordas_color = selected.name
            result.color_hex = extract_color_from_name(selected.name)
        elif selected.remark == "blessing":
            result.blessing = selected.name
        elif selected.remark == "entry":
            result.entry = selected.name
        
        # 继续递归
        self._draw_sub_items(selected.id, result, rng)
    
    def perform_draw(self, seed=None) -> BlessingResult:
        """执行抽签"""
        rng = random.Random(seed)
        result = BlessingResult()

        # 1. 抽取背景图
        bg_items = [item for item in DRAW_ITEMS if item.remark == "backgroundimg"]
        bg_item = self._draw_random_item(bg_items, rng)
        result.background_image = BACKGROUND_IMAGE_MAP.get(bg_item.name, "")
        result.background_id = bg_item.name

        # 2. 抽取签文类型
        text_items = self._get_children("0")
        if not text_items:
            text_items = self._get_children("9")
        text_items = [item for item in text_items if item.remark == "textimg"]
        text_item = self._draw_random_item(text_items, rng)
        result.text_image = TEXT_IMAGE_MAP.get(text_item.name, "")
        result.fortune_level = text_item.name

        # 3. 递归抽取下级项
        self._draw_sub_items(text_item.id, result, rng)

        return result
    
    def _hex_to_rgba(self, hex_color: str, alpha: int = 204) -> Tuple[int, int, int, int]:
        """将十六进制颜色转为 RGBA 元组"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)
    
    def generate_blessing_image(self, debug: bool = False) -> bytes:
        result = self.perform_draw()
        return self.generate_blessing_image_from_result(result, debug=debug)

    def generate_blessing_image_from_result(self, result: BlessingResult, debug: bool = False) -> bytes:
        if debug:
            print("--- 抽签结果 (Debug) ---")
            print(f"背景图: {result.background_image}")
            print(f"签文图: {result.text_image}")
            print(f"{result.dordas}")
            print(f"{result.dordas_color} ({result.color_hex})")
            print(f"祝福语: {result.blessing}")
            print(f"{result.entry}")
            print("-" * 26)

        # 创建画布
        canvas = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        
        # 1. 先绘制带颜色的背景层（使用 background.png 作为遮罩）
        self._draw_colored_background(canvas, result.color_hex)
        
        # 2. 绘制背景装饰层
        if result.background_image:
            self._draw_background_decoration(canvas, result.background_image)
        
        # 3. 绘制签文图片（大吉、中吉等）
        if result.text_image:
            self._draw_text_image(canvas, result.text_image)
        
        # 4. 绘制文字内容
        self._draw_texts(canvas, result)
        
        # 5. 转换为 PNG 字节流
        output = io.BytesIO()
        canvas.save(output, format='PNG')
        output.seek(0)
        return output.getvalue()
    
    def _draw_background_decoration(self, canvas: Image.Image, decoration_filename: str):
        """
        绘制装饰层，使用 background.png 的 alpha 通道作为遮罩，背景色为 color_hex，不透明
        """
        mask_path = self.assets_dir / "image" / decoration_filename
        try:
            base_texture = Image.open(mask_path).convert('RGBA')
            canvas.alpha_composite(base_texture)
        except Exception as e:
            print(f"警告：绘制装饰层失败 {e}")




    
    def _draw_colored_background(self, canvas: Image.Image, color_hex: str):
        """
        绘制背景层，使用 background.png 的 alpha 通道作为遮罩，背景色为 color_hex，不透明
        """
        mask_path = self.assets_dir / "image" / "background.png"
        try:
            # 加载遮罩图片，保持 RGBA
            mask_img = Image.open(mask_path).convert('RGBA')
            
            # 取出 alpha 通道作为遮罩
            alpha_mask = mask_img.split()[-1]  # alpha 通道
            
            # 创建纯色背景层，大小与画布一致，颜色为 color_hex，不透明
            color_layer = Image.new('RGBA', (self.width, self.height), self._hex_to_rgba(color_hex, alpha=200))
            
            # 创建空白透明画布
            temp_canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            
            # 用 alpha 通道作为遮罩，将纯色背景粘贴到空白画布上
            temp_canvas.paste(color_layer, (0, 0), mask=alpha_mask)
            
            # 将结果合成到底层画布
            canvas.alpha_composite(temp_canvas)
            
        except Exception as e:
            print(f"警告：绘制背景层失败 {e}")

    
    def _draw_text_image(self, canvas: Image.Image, text_filename: str):
        """绘制签文图片（大吉、中吉等）"""
        text_img_path = self.assets_dir / "image" / text_filename
        try:
            text_img = Image.open(text_img_path).convert('RGBA')
            
            x = int(self.width * 0.204)  # 从0.35改为0.25，进一步左移
            y = int(self.height * 0.49)
            
            canvas.paste(text_img, (x, y), text_img)
        except Exception as e:
            print(f"警告：加载签文图失败 {e}")
    
    def _draw_texts(self, canvas: Image.Image, result: BlessingResult):
        """绘制文字内容"""
        font_normal = self._load_font(size=40)  # 普通字体（36pt）
        font_blod = self._load_font(size=45)  # 稍小字体（32pt，用于祝福语）
        draw = ImageDraw.Draw(canvas)
        
        # 文字颜色：白色
        text_color = (255, 255, 255, 255)
        
        # 准备文字内容（按顺序）
        texts = [
            result.dordas,        # 结缘物：花
            result.dordas_color,  # 缘彩：菖蒲
            result.blessing,      # 祝福语（稍小）
            result.entry          # 宜/忌
        ]
        
        # 右侧文字区域位置
        text_width_ratio = 0.35
        margin_right = 40
        text_area_x = int(self.width * (1 - text_width_ratio)) - margin_right - 133  # 左移 133px，避免与签文图重叠
        
        # 垂直居中，逐行绘制
        # 行间距：一二行靠近（+5），二三行分开（+25），三四行分开（+25）
        line_spacings = [20, 60, 85]  # 每行之后的间距
        
        # 计算总高度
        total_height = self.font_size * 3 + 32 + sum(line_spacings)  # 3行普通 + 1行大字 + 间距
        start_y = int((self.height - total_height) / 2) + 29  # 微调偏移
        
        current_y = start_y
        for i, text in enumerate(texts):
            if text:
                # 第三行（祝福语，索引2）使用大字体
                current_font = font_blod if i == 2 else font_normal
                
                
                # 绘制主文字（白色）
                draw.text((text_area_x, current_y), text, font=current_font, fill=text_color)
                
                # 累加 Y 坐标
                if i < len(line_spacings):
                    current_y += (32 if i == 2 else self.font_size) + line_spacings[i]