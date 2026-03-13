"""플래시 세일 템플릿 - 긴급 타임세일 (강렬한 이펙트)"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.templates.base import BaseTemplate
from backend.utils.image_processor import (
    fit_image_in_box, create_solid_background,
    add_rounded_rectangle, pil_to_numpy
)
from backend.utils.text_renderer import (
    get_font, draw_text_centered, draw_price_text, draw_badge,
    draw_strikethrough_price
)


class FlashSaleTemplate(BaseTemplate):
    """
    플래시 세일: 긴급감 + 깜빡임 + 카운트다운
    구간: 경고임팩트(0-1.5s) → 상품+가격(1.5-5s) → 카운트다운+CTA(5-7s)
    """

    def get_duration(self) -> float:
        return 7.0

    def make_frame(self, t: float) -> np.ndarray:
        # 깜빡이는 빨간 배경
        flash = 0.5 + 0.5 * math.sin(t * 8)
        r = int(40 + 30 * flash)
        bg = create_solid_background(self.WIDTH, self.HEIGHT, (r, 5, 8, 255))
        draw = ImageDraw.Draw(bg)

        # 스캔라인 이펙트 (TV 느낌)
        self._draw_scanlines(bg, t)

        if t < 1.5:
            self._draw_warning_impact(draw, bg, t)
        elif t < 5.0:
            self._draw_product_section(draw, bg, t)
        else:
            self._draw_countdown_cta(draw, bg, t)

        # 깜빡이는 테두리
        border_alpha = 0.5 + 0.5 * math.sin(t * 10)
        self.draw_animated_border(bg, t,
                                  color=(255, int(200 * border_alpha), 0),
                                  width=8)
        self.draw_vignette(bg, 0.4)
        return pil_to_numpy(bg)

    def _draw_scanlines(self, img: Image.Image, t: float):
        """TV 스캔라인 이펙트"""
        draw = ImageDraw.Draw(img)
        offset = int(t * 100) % 8
        for y in range(offset, self.HEIGHT, 8):
            draw.line([(0, y), (self.WIDTH, y)], fill=(0, 0, 0, 30), width=1)

    def _draw_warning_impact(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        # 화면 플래시 (대형)
        if t < 0.15:
            self.draw_screen_flash(img, 0.9, (255, 255, 0))
        elif t < 0.3:
            self.draw_screen_flash(img, 0.5 * (0.3 - t) / 0.15, (255, 200, 0))

        # ⚡ FLASH SALE ⚡ 바운스 등장
        if t < 0.8 or int(t * 6) % 2 == 0:
            self.draw_glow_text(
                img, int(self.HEIGHT * 0.25),
                "⚡ FLASH SALE ⚡", 80,
                color=(255, 255, 0),
                glow_color=(255, 200, 0), glow_radius=15
            )

        # "지금 아니면 없다!" 흔들리며 등장
        if t > 0.3:
            shake = int(5 * math.sin(t * 20) * max(0, 1 - (t - 0.3) / 0.5))
            self.draw_bounce_text(
                ImageDraw.Draw(img),
                int(self.HEIGHT * 0.42) + shake,
                "지금 아니면 없다!", 60, t - 0.3,
                color=(255, 220, 220)
            )

        # 타이머 아이콘 + 펄스
        if t > 0.6:
            pulse = 0.8 + 0.2 * math.sin(t * 8)
            font3 = get_font(max(1, int(120 * pulse)), bold=True)
            draw_text_centered(ImageDraw.Draw(img), int(self.HEIGHT * 0.55),
                              "⏰", font3, self.WIDTH, shadow=False)

        # 긴급 경고 사운드 느낌 줄무늬
        if t < 0.5:
            stripe_w = 60
            for x in range(0, self.WIDTH + stripe_w, stripe_w * 2):
                xp = int(x + t * 200) % (self.WIDTH + stripe_w * 2) - stripe_w
                draw.polygon(
                    [(xp, self.HEIGHT - 100), (xp + stripe_w, self.HEIGHT - 100),
                     (xp + stripe_w - 20, self.HEIGHT), (xp - 20, self.HEIGHT)],
                    fill=(255, 200, 0, 200)
                )

        self.draw_particles(img, t, color_override=(255, 200, 50), intensity=0.8)

    def _draw_product_section(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 1.5

        # 상단 노란 배너 (슬라이드인)
        banner_ease = self.ease_out(min(1.0, dt / 0.3))
        banner_w = int(self.WIDTH * banner_ease)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, 0), (banner_w, 100)], fill=(255, 220, 0, 230))
        img.paste(Image.alpha_composite(img, overlay))
        draw = ImageDraw.Draw(img)

        if banner_ease > 0.5:
            font_banner = get_font(44, bold=True)
            draw_text_centered(draw, 22, "⚡ FLASH SALE ⚡",
                              font_banner, self.WIDTH,
                              fill=(180, 0, 0), shadow=False)

        # 상품 이미지 (줌인 등장)
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 140,
                int(self.HEIGHT * 0.38)
            )
            ease = min(1.0, dt / 0.5)
            self.draw_zoom_product(
                img, product_img, dt,
                center_y=int(self.HEIGHT * 0.32),
                zoom_start=0.4, zoom_end=1.0, ease_t=ease
            )

        draw = ImageDraw.Draw(img)

        # 상품명
        if dt > 0.2:
            font_name = get_font(50, bold=True)
            name_ease = self.ease_out(min(1.0, (dt - 0.2) / 0.4))
            draw_text_centered(draw, int(self.HEIGHT * 0.55 + 20 * (1 - name_ease)),
                              self.get_product_name(), font_name, self.WIDTH)

        # 원가 (취소선)
        if dt > 0.4 and self.get_original_price():
            draw_strikethrough_price(draw, int(self.HEIGHT * 0.63),
                                   self.format_price(self.get_original_price()),
                                   self.WIDTH, 36)

        # 할인가 (글로우 + 펄스)
        if dt > 0.5:
            price_text = self.format_price(self.get_price())
            pulse = 0.95 + 0.05 * math.sin(dt * 6)
            self.draw_glow_text(
                img, int(self.HEIGHT * 0.68), price_text,
                int(80 * pulse),
                color=(255, 255, 0),
                glow_color=(255, 150, 0), glow_radius=12
            )

        # 남은 수량 배지 (랜덤 느낌)
        if dt > 1.0:
            blink = 1 if int(t * 3) % 2 == 0 else 0.7
            font_qty = get_font(36, bold=True)
            draw = ImageDraw.Draw(img)
            draw_text_centered(draw, int(self.HEIGHT * 0.80),
                              "🔥 한정 수량 🔥", font_qty, self.WIDTH,
                              fill=(255, int(200 * blink), int(100 * blink)))

        self.draw_sparkles(img, t, int(self.HEIGHT * 0.5), int(self.HEIGHT * 0.3))

    def _draw_countdown_cta(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 5.0
        remaining = max(0, 7.0 - t)

        # 상품 유지 (작게)
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0], int(self.WIDTH * 0.4), int(self.HEIGHT * 0.18)
            )
            x = (self.WIDTH - product_img.width) // 2
            img.paste(product_img, (x, 30), product_img)

        draw = ImageDraw.Draw(img)

        # 가격
        price_text = self.format_price(self.get_price())
        self.draw_glow_text(img, int(self.HEIGHT * 0.28), price_text, 70,
                           color=(255, 255, 0), glow_color=(255, 150, 0))

        # 카운트다운 (대형, 빨간색)
        countdown_text = f"{remaining:.1f}"
        draw = ImageDraw.Draw(img)

        # 큰 숫자
        font_cd = get_font(200, bold=True)
        blink = 1 if int(t * 4) % 2 == 0 else 0.6
        cd_color = (255, int(50 * blink), int(50 * blink))
        draw_text_centered(draw, int(self.HEIGHT * 0.42), countdown_text,
                          font_cd, self.WIDTH, fill=cd_color)

        # "초 남음" 텍스트
        font_label = get_font(44, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.62), "초 남음!",
                          font_label, self.WIDTH,
                          fill=(255, 200, 200))

        # 프로그레스 바
        bar_y = int(self.HEIGHT * 0.70)
        bar_w = self.WIDTH - 120
        bar_h = 24
        progress = remaining / 2.0  # 2초 카운트다운 구간
        # 배경
        draw.rounded_rectangle(
            [(60, bar_y), (60 + bar_w, bar_y + bar_h)],
            radius=12, fill=(80, 0, 0)
        )
        # 게이지
        fill_w = int(bar_w * min(1.0, progress))
        if fill_w > 0:
            draw.rounded_rectangle(
                [(60, bar_y), (60 + fill_w, bar_y + bar_h)],
                radius=12, fill=(255, int(200 * blink), 0)
            )

        # CTA 버튼 (펄스)
        pulse = 0.93 + 0.07 * math.sin(dt * 10)
        btn_w = int((self.WIDTH - 160) * pulse)
        btn_x = (self.WIDTH - btn_w) // 2
        btn_y = int(self.HEIGHT * 0.78)
        bg_btn = add_rounded_rectangle(
            img, btn_x, btn_y, btn_w, 110, 55,
            (255, 220, 0, 240)
        )
        img.paste(bg_btn)
        draw = ImageDraw.Draw(img)
        font_cta = get_font(46, bold=True)
        draw_text_centered(draw, btn_y + 22,
                          "👆 지금 바로 구매!", font_cta, self.WIDTH,
                          fill=(120, 0, 0), shadow=False)

        # 제휴 링크
        self.draw_affiliate_bar(img, t, fade_start=5.0)

        # 파티클 + 긴급감
        self.draw_particles(img, t, color_override=(255, 100, 50), intensity=1.0)
