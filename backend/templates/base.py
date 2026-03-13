"""숏폼 영상 템플릿 베이스 클래스 - 다이나믹 이펙트 포함"""
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.utils.image_processor import (
    VIDEO_WIDTH, VIDEO_HEIGHT, pil_to_numpy,
    create_gradient_background, create_solid_background
)
from backend.utils.text_renderer import get_font, draw_text_centered


class BaseTemplate(ABC):
    """모든 숏폼 템플릿의 베이스 클래스 - 풍부한 이펙트"""

    WIDTH = VIDEO_WIDTH    # 1080
    HEIGHT = VIDEO_HEIGHT  # 1920
    FPS = 30

    def __init__(self, product_data: dict, image_paths: list[str]):
        self.product = product_data
        self.image_paths = image_paths
        self.duration = self.get_duration()
        # 파티클 시드 (일관된 랜덤)
        self._rng = np.random.RandomState(42)
        self._particles = self._init_particles(40)
        self._sparkles = self._init_particles(25)

    def _init_particles(self, n: int) -> list:
        """파티클 초기 위치/속도 생성"""
        particles = []
        for _ in range(n):
            particles.append({
                'x': self._rng.randint(0, self.WIDTH),
                'y': self._rng.randint(0, self.HEIGHT),
                'vx': self._rng.uniform(-50, 50),
                'vy': self._rng.uniform(-200, -30),
                'size': self._rng.randint(3, 12),
                'color': (
                    self._rng.randint(200, 256),
                    self._rng.randint(150, 256),
                    self._rng.randint(50, 256),
                ),
                'life': self._rng.uniform(0.3, 1.0),
                'phase': self._rng.uniform(0, 2 * math.pi),
            })
        return particles

    @abstractmethod
    def get_duration(self) -> float:
        pass

    @abstractmethod
    def make_frame(self, t: float) -> np.ndarray:
        pass

    def get_product_name(self) -> str:
        return self.product.get("name", "상품명")

    def get_price(self) -> str:
        return self.product.get("price", "0")

    def get_original_price(self) -> str:
        return self.product.get("original_price", "")

    def get_description(self) -> str:
        return self.product.get("description", "")

    def get_features(self) -> list[str]:
        return self.product.get("features", [])

    def get_review(self) -> str:
        return self.product.get("review", "")

    def get_cta(self) -> str:
        return self.product.get("cta", "지금 바로 구매하세요!")

    def get_affiliate_id(self) -> str:
        return self.product.get("affiliate_id", "")

    def get_affiliate_link(self) -> str:
        return self.product.get("affiliate_link", "")

    def draw_affiliate_bar(self, img: Image.Image, t: float,
                           y: int = 0, fade_start: float = 0.0):
        """하단에 제휴마케팅 ID + 링크 바 표시"""
        aff_id = self.get_affiliate_id()
        aff_link = self.get_affiliate_link()
        if not aff_id and not aff_link:
            return

        if y <= 0:
            y = int(self.HEIGHT * 0.93)

        # 페이드인
        alpha = 1.0
        if fade_start > 0 and t > fade_start:
            alpha = min(1.0, (t - fade_start) / 0.5)
        else:
            alpha = 1.0

        # 반투명 배경 바
        bar_h = 90
        overlay = Image.new("RGBA", (self.WIDTH, bar_h), (0, 0, 0, int(160 * alpha)))
        img.paste(Image.alpha_composite(
            img.crop((0, y, self.WIDTH, y + bar_h)).convert("RGBA"), overlay
        ), (0, y))

        draw = ImageDraw.Draw(img)
        text_alpha = int(255 * alpha)

        if aff_id:
            font_id = get_font(30, bold=True)
            draw_text_centered(draw, y + 10, f"@{aff_id}",
                              font_id, self.WIDTH,
                              fill=(255, 255, 255, text_alpha))
        if aff_link:
            font_link = get_font(26)
            link_y = y + 48 if aff_id else y + 25
            draw_text_centered(draw, link_y, f"🔗 {aff_link}",
                              font_link, self.WIDTH,
                              fill=(180, 220, 255, text_alpha))

    def format_price(self, price_str: str) -> str:
        try:
            num = int(price_str.replace(",", "").replace("원", ""))
            return f"{num:,}원"
        except (ValueError, AttributeError):
            return price_str

    # ---- 이징 함수 ----
    @staticmethod
    def ease_in_out(t: float) -> float:
        if t < 0.5:
            return 2 * t * t
        return 1 - (-2 * t + 2) ** 2 / 2

    @staticmethod
    def ease_out(t: float) -> float:
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in(t: float) -> float:
        return t * t * t

    @staticmethod
    def ease_out_back(t: float) -> float:
        """오버슈트 바운스"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """바운스 이펙트"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """탄성 이펙트"""
        if t == 0 or t == 1:
            return t
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * max(0, min(1, t))

    @staticmethod
    def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        return max(min_val, min(max_val, value))

    # ---- 비주얼 이펙트 ----
    def draw_particles(self, img: Image.Image, t: float,
                       color_override: tuple = None, intensity: float = 1.0):
        """반짝이는 파티클 이펙트"""
        draw = ImageDraw.Draw(img)
        for p in self._particles:
            age = (t + p['phase']) % p['life']
            alpha = max(0, 1 - age / p['life']) * intensity
            if alpha < 0.1:
                continue
            x = (p['x'] + p['vx'] * t) % self.WIDTH
            y = (p['y'] + p['vy'] * t) % self.HEIGHT
            size = int(p['size'] * alpha)
            if size < 1:
                continue
            color = color_override or p['color']
            r, g, b = color
            draw.ellipse(
                [int(x) - size, int(y) - size, int(x) + size, int(y) + size],
                fill=(r, g, b, int(200 * alpha))
            )

    def draw_sparkles(self, img: Image.Image, t: float,
                      region_y: int = 0, region_h: int = None):
        """빛나는 스파클 이펙트 (십자가 모양)"""
        if region_h is None:
            region_h = self.HEIGHT
        draw = ImageDraw.Draw(img)
        for i, p in enumerate(self._sparkles):
            phase = t * 3 + p['phase']
            alpha = (math.sin(phase) + 1) / 2
            if alpha < 0.3:
                continue
            x = (p['x'] + int(math.sin(t * 0.5 + i) * 30)) % self.WIDTH
            y = region_y + (p['y'] % region_h)
            size = int(p['size'] * 1.5 * alpha)
            c = int(255 * alpha)
            # 십자가 스파클
            draw.line([(x - size, y), (x + size, y)], fill=(c, c, c, int(200 * alpha)), width=2)
            draw.line([(x, y - size), (x, y + size)], fill=(c, c, c, int(200 * alpha)), width=2)

    def draw_moving_gradient_bg(self, t: float, color1: tuple, color2: tuple,
                                 color3: tuple = None) -> Image.Image:
        """움직이는 그라데이션 배경 (벡터화)"""
        c3 = color3 or tuple(max(0, min(255, (a + b) // 2 + 30)) for a, b in zip(color1, color2))
        shift = math.sin(t * 0.8) * 0.2
        arr = np.zeros((self.HEIGHT, self.WIDTH, 4), dtype=np.uint8)
        ratios = np.linspace(0, 1, self.HEIGHT) + shift
        ratios = np.clip(ratios, 0, 1)
        for ch in range(3):
            below = ratios < 0.5
            above = ~below
            # 상단 절반: color1 → c3
            r2 = ratios[below] * 2
            arr[below, :, ch] = np.clip(
                color1[ch] + (c3[ch] - color1[ch]) * r2, 0, 255
            ).astype(np.uint8)[:, np.newaxis]
            # 하단 절반: c3 → color2
            r2 = (ratios[above] - 0.5) * 2
            arr[above, :, ch] = np.clip(
                c3[ch] + (color2[ch] - c3[ch]) * r2, 0, 255
            ).astype(np.uint8)[:, np.newaxis]
        arr[:, :, 3] = 255
        return Image.fromarray(arr, "RGBA")

    def draw_screen_flash(self, img: Image.Image, intensity: float,
                          color: tuple = (255, 255, 255)):
        """화면 플래시 이펙트"""
        if intensity < 0.01:
            return
        overlay = Image.new("RGBA", img.size,
                           (*color, int(min(255, 255 * intensity))))
        img.paste(Image.alpha_composite(img, overlay))

    def draw_vignette(self, img: Image.Image, intensity: float = 0.4):
        """비네팅 이펙트 (가장자리 어둡게) - 간소화"""
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        # 심플 테두리 어두움
        border = int(self.WIDTH * 0.08)
        alpha = int(80 * intensity)
        draw.rectangle([(0, 0), (border, self.HEIGHT)], fill=(0, 0, 0, alpha))
        draw.rectangle([(self.WIDTH - border, 0), (self.WIDTH, self.HEIGHT)], fill=(0, 0, 0, alpha))
        draw.rectangle([(0, 0), (self.WIDTH, border)], fill=(0, 0, 0, alpha))
        draw.rectangle([(0, self.HEIGHT - border), (self.WIDTH, self.HEIGHT)], fill=(0, 0, 0, alpha))
        img.paste(Image.alpha_composite(img, overlay))

    def draw_animated_border(self, img: Image.Image, t: float,
                             color: tuple = (255, 200, 50), width: int = 8):
        """애니메이션 테두리"""
        draw = ImageDraw.Draw(img)
        progress = (t * 0.5) % 1.0
        dash_len = 60
        gap_len = 30
        total = dash_len + gap_len

        # 상단
        for x in range(0, self.WIDTH, total):
            sx = (x + int(progress * total)) % self.WIDTH
            ex = min(sx + dash_len, self.WIDTH)
            draw.rectangle([sx, 0, ex, width], fill=(*color, 200))
        # 하단
        for x in range(0, self.WIDTH, total):
            sx = (x + int(progress * total)) % self.WIDTH
            ex = min(sx + dash_len, self.WIDTH)
            draw.rectangle([sx, self.HEIGHT - width, ex, self.HEIGHT], fill=(*color, 200))

    def draw_confetti(self, img: Image.Image, t: float, start_t: float = 0):
        """컨페티/축하 이펙트"""
        draw = ImageDraw.Draw(img)
        dt = t - start_t
        if dt < 0:
            return
        colors = [(255, 69, 58), (255, 200, 50), (50, 200, 255),
                  (100, 255, 100), (255, 100, 200), (255, 150, 0)]
        for i in range(30):
            seed = (i * 7 + 13) % 100
            x = (seed * self.WIDTH // 100 + int(math.sin(dt * 2 + i) * 50)) % self.WIDTH
            y = int(-50 + (dt * 300 + seed * 5) % (self.HEIGHT + 100))
            rot = math.sin(dt * 4 + i * 0.5) * 0.5
            size = 6 + (seed % 8)
            color = colors[i % len(colors)]
            # 사각형 컨페티
            cx, cy = x, y
            points = [
                (cx - size, cy - size * 2),
                (cx + size, cy - size * 2),
                (cx + size, cy + size * 2),
                (cx - size, cy + size * 2),
            ]
            alpha = max(0, min(255, int(255 * (1 - dt / 3))))
            draw.polygon(points, fill=(*color, alpha))

    def draw_zoom_product(self, img: Image.Image, product_img: Image.Image,
                          t: float, center_y: int, zoom_start: float = 0.5,
                          zoom_end: float = 1.0, ease_t: float = None):
        """줌 이펙트가 있는 상품 이미지 그리기"""
        if ease_t is None:
            ease_t = t
        scale = self.lerp(zoom_start, zoom_end, self.ease_out_back(min(1.0, ease_t)))
        new_w = int(product_img.width * scale)
        new_h = int(product_img.height * scale)
        if new_w < 1 or new_h < 1:
            return
        resized = product_img.resize((new_w, new_h), Image.LANCZOS)
        x = (self.WIDTH - new_w) // 2
        y = center_y - new_h // 2
        img.paste(resized, (x, y), resized)

    def draw_glow_text(self, img: Image.Image, y: int, text: str,
                       font_size: int, color: tuple = (255, 255, 255),
                       glow_color: tuple = (255, 200, 100), glow_radius: int = 8):
        """글로우 효과 텍스트"""
        font = get_font(font_size, bold=True)
        # 글로우 레이어
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        bbox = gd.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (self.WIDTH - tw) // 2
        gd.text((x, y), text, font=font, fill=(*glow_color, 180))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=glow_radius))
        img.paste(Image.alpha_composite(img, glow))
        # 본문
        draw = ImageDraw.Draw(img)
        draw.text((x, y), text, font=font, fill=color)

    def draw_bounce_text(self, draw: ImageDraw.Draw, y: int, text: str,
                         font_size: int, t: float,
                         color: tuple = (255, 255, 255)):
        """글자별 바운스 텍스트"""
        font = get_font(font_size, bold=True)
        total_w = draw.textbbox((0, 0), text, font=font)[2]
        start_x = (self.WIDTH - total_w) // 2
        x = start_x
        for i, ch in enumerate(text):
            delay = i * 0.05
            ct = max(0, t - delay)
            bounce = self.ease_out_bounce(min(1.0, ct * 3))
            offset_y = int(-30 * (1 - bounce))
            cw = draw.textbbox((0, 0), ch, font=font)[2]
            draw.text((x, y + offset_y), ch, font=font,
                     fill=color)
            x += cw
