"""가격 강조 템플릿 - 드라마틱 할인가 강조"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.templates.base import BaseTemplate
from backend.utils.image_processor import (
    fit_image_in_box, create_gradient_background,
    add_rounded_rectangle, pil_to_numpy
)
from backend.utils.text_renderer import (
    get_font, draw_text_centered, draw_price_text,
    draw_strikethrough_price, draw_badge
)


class PriceDropTemplate(BaseTemplate):
    """
    가격 드롭: 원가 → 할인가 드라마틱 전환 + 흔들림/플래시
    구간: 상품등장(0-2s) → 원가표시(2-3.5s) → 가격떨어짐(3.5-5.5s) → 할인결과+CTA(5.5-8s)
    """

    def get_duration(self) -> float:
        return 8.0

    def make_frame(self, t: float) -> np.ndarray:
        # 빨간 그라데이션 배경 (강렬)
        flash = math.sin(t * 3) * 0.1
        bg = self.draw_moving_gradient_bg(
            t, (160, 10, 10), (60, 0, 20), (100, 0, 30)
        )
        draw = ImageDraw.Draw(bg)

        if t < 2.0:
            self._draw_product_entrance(draw, bg, t)
        elif t < 3.5:
            self._draw_original_price(draw, bg, t)
        elif t < 5.5:
            self._draw_price_drop_impact(draw, bg, t)
        else:
            self._draw_final_deal(draw, bg, t)

        # 애니메이션 테두리
        self.draw_animated_border(bg, t, color=(255, 200, 50), width=6)
        self.draw_vignette(bg, 0.35)
        return pil_to_numpy(bg)

    def _draw_product_entrance(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        # 화면 플래시
        if t < 0.2:
            self.draw_screen_flash(img, (0.2 - t) / 0.2 * 0.5, (255, 100, 50))

        # 상품 이미지 줌인 등장
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 160,
                int(self.HEIGHT * 0.42)
            )
            ease = min(1.0, t / 0.7)
            self.draw_zoom_product(
                img, product_img, t,
                center_y=int(self.HEIGHT * 0.30),
                zoom_start=0.2, zoom_end=1.0, ease_t=ease
            )

        # 상품명 바운스
        if t > 0.3:
            self.draw_bounce_text(
                ImageDraw.Draw(img),
                int(self.HEIGHT * 0.56),
                self.get_product_name(), 56, t - 0.3,
                color=(255, 255, 255)
            )

        # "얼마일까?" 텍스트
        if t > 1.0:
            fade = self.ease_out(min(1.0, (t - 1.0) / 0.5))
            font_q = get_font(44, bold=True)
            pulse = 0.8 + 0.2 * math.sin(t * 6)
            draw_text_centered(
                ImageDraw.Draw(img), int(self.HEIGHT * 0.68),
                "💰 얼마일까요? 💰", font_q, self.WIDTH,
                fill=(255, int(255 * pulse), int(100 * pulse))
            )

        self.draw_sparkles(img, t, int(self.HEIGHT * 0.1), int(self.HEIGHT * 0.5))

    def _draw_original_price(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 2.0

        # 상품 이미지 (유지, 작게)
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0], int(self.WIDTH * 0.5), int(self.HEIGHT * 0.25)
            )
            x = (self.WIDTH - product_img.width) // 2
            img.paste(product_img, (x, int(self.HEIGHT * 0.05)), product_img)

        # 상품명
        font_name = get_font(44, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.33), self.get_product_name(),
                          font_name, self.WIDTH)

        # 원가 극적 등장 (커지면서)
        orig_price = self.get_original_price() or self.get_price()
        price_text = self.format_price(orig_price)

        scale = self.ease_out_elastic(min(1.0, dt / 0.6))
        font_size = int(70 * scale)
        font_size = max(20, min(100, font_size))
        font = get_font(font_size, bold=True)
        y = int(self.HEIGHT * 0.45)
        draw_text_centered(draw, y, price_text, font, self.WIDTH,
                          fill=(255, 255, 255))

        # "이 가격이..." 흔들리며 표시
        if dt > 0.5:
            shake = int(3 * math.sin(dt * 15))
            font_hint = get_font(40)
            draw_text_centered(draw, int(self.HEIGHT * 0.58) + shake,
                              "이 가격이 변한다면...?", font_hint, self.WIDTH,
                              fill=(255, 200, 150))

        self.draw_particles(img, t, color_override=(255, 150, 50), intensity=0.5)

    def _draw_price_drop_impact(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 3.5

        # 큰 화면 플래시 (떨어지는 순간!)
        if dt < 0.3:
            self.draw_screen_flash(img, (0.3 - dt) / 0.3 * 0.8, (255, 255, 0))

        # 화면 흔들림
        shake_x = int(15 * math.sin(dt * 40) * max(0, 1 - dt))
        shake_y = int(10 * math.cos(dt * 35) * max(0, 1 - dt))

        # 상품 이미지
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0], int(self.WIDTH * 0.45), int(self.HEIGHT * 0.22)
            )
            x = (self.WIDTH - product_img.width) // 2 + shake_x
            y = int(self.HEIGHT * 0.05) + shake_y
            img.paste(product_img, (x, y), product_img)

        draw = ImageDraw.Draw(img)

        # 원가 (취소선 + 빨간색으로 변화)
        orig_price = self.get_original_price() or self.get_price()
        orig_y = int(self.HEIGHT * 0.33) + shake_y
        draw_strikethrough_price(draw, orig_y,
                                self.format_price(orig_price),
                                self.WIDTH, 44)

        # 할인가 떨어지는 애니메이션 (위에서 아래로 + 바운스)
        drop_progress = self.ease_out_bounce(min(1.0, dt / 0.8))
        price_text = self.format_price(self.get_price())

        # 크기 변화 (크게 → 정상)
        size_mult = 1.0 + 0.5 * max(0, 1 - dt / 0.5)
        font_size = int(90 * size_mult)
        font_size = max(70, min(130, font_size))

        target_y = int(self.HEIGHT * 0.45)
        start_y = int(self.HEIGHT * -0.1)
        price_y = int(start_y + (target_y - start_y) * drop_progress) + shake_y

        # 글로우 할인가
        self.draw_glow_text(img, price_y, price_text, font_size,
                           color=(255, 255, 0),
                           glow_color=(255, 150, 0), glow_radius=15)
        draw = ImageDraw.Draw(img)

        # 할인율 배지 폭발 등장
        if dt > 0.4:
            badge_ease = self.ease_out_back(min(1.0, (dt - 0.4) / 0.5))
            discount = self._calc_discount()
            badge_text = f"  {discount}% OFF  " if discount else "  SALE  "
            badge_size = int(42 * badge_ease)
            if badge_size > 10:
                badge_y = int(self.HEIGHT * 0.60)
                bg_badge = draw_badge(
                    img, badge_text,
                    position=(self.WIDTH // 2 - 120, badge_y),
                    bg_color=(255, 220, 0, int(230 * badge_ease)),
                    text_color=(180, 0, 0),
                    font_size=badge_size
                )
                img.paste(bg_badge)

        # 컨페티 폭발
        self.draw_confetti(img, t, start_t=3.5)
        self.draw_particles(img, t, color_override=(255, 255, 100), intensity=1.0)

    def _draw_final_deal(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 5.5

        # 상품 이미지
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0], self.WIDTH - 200, int(self.HEIGHT * 0.30)
            )
            x = (self.WIDTH - product_img.width) // 2
            img.paste(product_img, (x, int(self.HEIGHT * 0.05)), product_img)

        draw = ImageDraw.Draw(img)

        # 상품명
        font_name = get_font(48, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.38), self.get_product_name(),
                          font_name, self.WIDTH)

        # 원가 (취소선)
        orig_price = self.get_original_price() or self.get_price()
        draw_strikethrough_price(draw, int(self.HEIGHT * 0.46),
                                self.format_price(orig_price), self.WIDTH, 40)

        # 할인가 (글로우)
        price_text = self.format_price(self.get_price())
        self.draw_glow_text(img, int(self.HEIGHT * 0.52), price_text, 80,
                           color=(255, 255, 0),
                           glow_color=(255, 180, 0), glow_radius=12)

        # 할인율
        discount = self._calc_discount()
        if discount:
            draw = ImageDraw.Draw(img)
            font_disc = get_font(60, bold=True)
            pulse = 0.8 + 0.2 * math.sin(dt * 6)
            draw_text_centered(draw, int(self.HEIGHT * 0.66),
                              f"🔥 {discount}% 할인! 🔥",
                              font_disc, self.WIDTH,
                              fill=(255, int(255 * pulse), int(50 * pulse)))

        # CTA 버튼
        pulse = 0.95 + 0.05 * math.sin(dt * 8)
        btn_w = int((self.WIDTH - 200) * pulse)
        btn_x = (self.WIDTH - btn_w) // 2
        btn_y = int(self.HEIGHT * 0.78)
        bg_btn = add_rounded_rectangle(
            img, btn_x, btn_y, btn_w, 110, 55,
            (255, 50, 30, 230)
        )
        img.paste(bg_btn)
        draw = ImageDraw.Draw(img)
        font_cta = get_font(44, bold=True)
        draw_text_centered(draw, btn_y + 25, self.get_cta(),
                          font_cta, self.WIDTH, fill=(255, 255, 255))

        # 하단 힌트
        arrow_off = int(math.sin(dt * 4) * 12)
        font_hint = get_font(30)
        draw_text_centered(draw, int(self.HEIGHT * 0.92) + arrow_off,
                          "👆 놓치지 마세요!", font_hint, self.WIDTH,
                          fill=(255, 200, 200))

        # 제휴 링크
        self.draw_affiliate_bar(img, t, fade_start=5.5)

        self.draw_sparkles(img, t, int(self.HEIGHT * 0.5), int(self.HEIGHT * 0.4))

    def _calc_discount(self) -> int:
        try:
            orig = int(self.get_original_price().replace(",", "").replace("원", ""))
            sale = int(self.get_price().replace(",", "").replace("원", ""))
            return int((1 - sale / orig) * 100)
        except (ValueError, ZeroDivisionError, AttributeError):
            return 0
