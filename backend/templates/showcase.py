"""상품 쇼케이스 템플릿 - 다이나믹 상품 소개"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.templates.base import BaseTemplate
from backend.utils.image_processor import (
    fit_image_in_box, create_gradient_background,
    add_rounded_rectangle, pil_to_numpy
)
from backend.utils.text_renderer import (
    get_font, draw_text_centered, draw_price_text, draw_badge
)


class ShowcaseTemplate(BaseTemplate):
    """
    상품 쇼케이스: 임팩트 있는 등장 + 상품 이미지 + 정보
    구간: 임팩트 인트로(0-1.5s) → 상품 줌인(1.5-5s) → 정보 슬라이드(5-8s) → CTA 펄스(8-10s)
    """

    def get_duration(self) -> float:
        return 10.0

    def make_frame(self, t: float) -> np.ndarray:
        # 움직이는 그라데이션 배경
        bg = self.draw_moving_gradient_bg(t, (15, 10, 40), (50, 15, 70), (30, 5, 60))
        draw = ImageDraw.Draw(bg)

        # 애니메이션 테두리
        self.draw_animated_border(bg, t, color=(180, 120, 255), width=6)

        if t < 1.5:
            self._draw_intro(draw, bg, t)
        elif t < 5.0:
            self._draw_product_reveal(draw, bg, t)
        elif t < 8.0:
            self._draw_info_slide(draw, bg, t)
        else:
            self._draw_cta(draw, bg, t)

        # 비네팅
        self.draw_vignette(bg, 0.3)
        return pil_to_numpy(bg)

    def _draw_intro(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        # 화면 플래시 (0~0.3초)
        if t < 0.3:
            self.draw_screen_flash(img, (0.3 - t) / 0.3 * 0.6, (180, 120, 255))

        # 상품명 바운스 등장
        progress = min(1.0, t / 0.8)
        if progress > 0:
            self.draw_bounce_text(
                ImageDraw.Draw(img),
                int(self.HEIGHT * 0.35),
                self.get_product_name(),
                72, t,
                color=(255, 255, 255)
            )

        # 글로우 서브타이틀
        if t > 0.5:
            sub_alpha = self.ease_out(min(1.0, (t - 0.5) / 0.6))
            desc = self.get_description() or "프리미엄 상품"
            font_sub = get_font(36)
            c = int(200 * sub_alpha)
            draw_text_centered(draw, int(self.HEIGHT * 0.45),
                              f"✨ {desc} ✨", font_sub, self.WIDTH,
                              fill=(c, c, int(255 * sub_alpha)))

        # 가격 미리보기
        if t > 0.8:
            price_alpha = self.ease_out(min(1.0, (t - 0.8) / 0.5))
            price_text = self.format_price(self.get_price())
            font_price = get_font(64, bold=True)
            bounce = self.ease_out_elastic(min(1.0, (t - 0.8) / 0.7))
            scale_y = int(self.HEIGHT * 0.55 - 20 * (1 - bounce))
            draw_text_centered(draw, scale_y, price_text,
                              font_price, self.WIDTH,
                              fill=(255, int(100 * price_alpha), int(80 * price_alpha)))

        # 스파클
        self.draw_sparkles(img, t, int(self.HEIGHT * 0.3), int(self.HEIGHT * 0.4))

    def _draw_product_reveal(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 1.5

        # 화면 플래시 (제품 등장)
        if dt < 0.2:
            self.draw_screen_flash(img, (0.2 - dt) / 0.2 * 0.4)

        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 100,
                int(self.HEIGHT * 0.55)
            )
            # 줌 + 바운스 등장
            ease = min(1.0, dt / 0.6)
            self.draw_zoom_product(
                img, product_img, dt,
                center_y=int(self.HEIGHT * 0.38),
                zoom_start=0.3, zoom_end=1.0,
                ease_t=ease
            )

        # 상품명 (하단)
        if dt > 0.3:
            name_ease = self.ease_out(min(1.0, (dt - 0.3) / 0.5))
            name_y = int(self.HEIGHT * 0.70 + 30 * (1 - name_ease))
            font_name = get_font(56, bold=True)
            draw_text_centered(draw, name_y, self.get_product_name(),
                              font_name, self.WIDTH)

        # 슬로우 줌 펄스 (유지 구간)
        if dt > 1.0 and self.image_paths:
            pulse = 1.0 + 0.02 * math.sin(dt * 2)
            product_img = fit_image_in_box(
                self.image_paths[0],
                int((self.WIDTH - 100) * pulse),
                int(self.HEIGHT * 0.55 * pulse)
            )
            x = (self.WIDTH - product_img.width) // 2
            y = int(self.HEIGHT * 0.38) - product_img.height // 2
            img.paste(product_img, (x, y), product_img)

        # 파티클 배경
        self.draw_particles(img, t, color_override=(180, 120, 255), intensity=0.6)

    def _draw_info_slide(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 5.0
        slide_ease = self.ease_out_back(min(1.0, dt / 0.6))

        # 상품 이미지 (축소하여 상단)
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                int(self.WIDTH * 0.6),
                int(self.HEIGHT * 0.30)
            )
            x = (self.WIDTH - product_img.width) // 2
            y = int(self.HEIGHT * 0.05)
            img.paste(product_img, (x, y), product_img)

        # 정보 카드 (슬라이드업)
        card_y = int(self.HEIGHT * 0.40 + 80 * (1 - slide_ease))
        card_h = int(self.HEIGHT * 0.48)
        bg_card = add_rounded_rectangle(
            img, 40, card_y, self.WIDTH - 80, card_h, 30,
            (0, 0, 0, int(180 * slide_ease))
        )
        img.paste(bg_card)
        draw2 = ImageDraw.Draw(img)

        # 상품명
        font_name = get_font(52, bold=True)
        draw_text_centered(draw2, card_y + 40, self.get_product_name(),
                          font_name, self.WIDTH)

        # 구분선
        line_y = card_y + 110
        line_w = int((self.WIDTH - 200) * min(1.0, (dt - 0.2) / 0.3))
        if line_w > 0:
            draw2.line(
                [(self.WIDTH // 2 - line_w // 2, line_y),
                 (self.WIDTH // 2 + line_w // 2, line_y)],
                fill=(180, 120, 255, 200), width=3
            )

        # 가격 (글로우)
        if dt > 0.3:
            price_text = self.format_price(self.get_price())
            self.draw_glow_text(img, card_y + 140, price_text, 72,
                               color=(255, 100, 80),
                               glow_color=(255, 50, 50), glow_radius=10)
            draw2 = ImageDraw.Draw(img)

        # 설명
        if dt > 0.5:
            desc = self.get_description()
            if desc:
                desc_ease = self.ease_out(min(1.0, (dt - 0.5) / 0.4))
                font_desc = get_font(34)
                draw_text_centered(draw2, card_y + 250,
                                  desc, font_desc, self.WIDTH,
                                  fill=(200, 200, 200))

        # 원가 vs 할인가
        if dt > 0.7 and self.get_original_price():
            from backend.utils.text_renderer import draw_strikethrough_price
            draw_strikethrough_price(draw2, card_y + 310,
                                   self.format_price(self.get_original_price()),
                                   self.WIDTH, 36)

        # 스파클
        self.draw_sparkles(img, t, card_y, card_h)

    def _draw_cta(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 8.0

        # 상품 이미지
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 200,
                int(self.HEIGHT * 0.35)
            )
            x = (self.WIDTH - product_img.width) // 2
            img.paste(product_img, (x, int(self.HEIGHT * 0.08)), product_img)

        # 가격
        price_text = self.format_price(self.get_price())
        self.draw_glow_text(img, int(self.HEIGHT * 0.50), price_text, 80,
                           color=(255, 80, 60),
                           glow_color=(255, 50, 30), glow_radius=12)

        # CTA 버튼 (펄스)
        pulse = 0.9 + 0.1 * math.sin(dt * 8)
        btn_w = int((self.WIDTH - 200) * pulse)
        btn_x = (self.WIDTH - btn_w) // 2
        btn_y = int(self.HEIGHT * 0.65)
        bg_btn = add_rounded_rectangle(
            img, btn_x, btn_y, btn_w, 110, 55,
            (200, 50, 255, int(220 + 35 * math.sin(dt * 6)))
        )
        img.paste(bg_btn)
        draw2 = ImageDraw.Draw(img)
        font_cta = get_font(44, bold=True)
        draw_text_centered(draw2, btn_y + 25, self.get_cta(),
                          font_cta, self.WIDTH, fill=(255, 255, 255))

        # "스와이프" 안내
        swipe_y = int(self.HEIGHT * 0.82)
        arrow_offset = int(math.sin(dt * 4) * 15)
        font_swipe = get_font(32)
        draw_text_centered(draw2, swipe_y + arrow_offset, "👆 지금 바로!",
                          font_swipe, self.WIDTH, fill=(200, 200, 255))

        # 제휴 링크
        self.draw_affiliate_bar(img, t, fade_start=8.0)

        # 컨페티
        self.draw_confetti(img, t, start_t=8.0)
        # 파티클
        self.draw_particles(img, t, color_override=(200, 150, 255))
