"""베스트 리뷰 템플릿 - 임팩트 리뷰/후기 강조"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.templates.base import BaseTemplate
from backend.utils.image_processor import (
    fit_image_in_box, create_gradient_background,
    add_rounded_rectangle, pil_to_numpy
)
from backend.utils.text_renderer import (
    get_font, draw_text_centered, draw_price_text, wrap_text
)


class BestReviewTemplate(BaseTemplate):
    """
    베스트 리뷰: 리뷰 텍스트 + 상품 강조
    구간: 상품임팩트(0-2.5s) → 리뷰타이핑(2.5-7s) → 구매유도(7-10s)
    """

    def get_duration(self) -> float:
        return 10.0

    def make_frame(self, t: float) -> np.ndarray:
        bg = self.draw_moving_gradient_bg(t, (8, 8, 30), (25, 8, 45), (15, 15, 35))
        draw = ImageDraw.Draw(bg)

        if t < 2.5:
            self._draw_product_section(draw, bg, t)
        elif t < 7.0:
            self._draw_review_section(draw, bg, t)
        else:
            self._draw_purchase_section(draw, bg, t)

        self.draw_animated_border(bg, t, color=(255, 200, 80), width=5)
        self.draw_vignette(bg, 0.3)
        return pil_to_numpy(bg)

    def _draw_product_section(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        # 플래시 등장
        if t < 0.2:
            self.draw_screen_flash(img, (0.2 - t) / 0.2 * 0.5, (255, 200, 100))

        # 별점 애니메이션 (하나씩 등장)
        stars_text = ""
        for i in range(5):
            if t > i * 0.15:
                stars_text += "★"
            else:
                stars_text += "☆"
        font_stars = get_font(60)
        draw_text_centered(draw, int(self.HEIGHT * 0.06), stars_text,
                          font_stars, self.WIDTH,
                          fill=(255, 200, 0), shadow=False)

        # BEST REVIEW 글로우
        if t > 0.3:
            self.draw_glow_text(
                img, int(self.HEIGHT * 0.14),
                "🏆 BEST REVIEW 🏆", 52,
                color=(255, 220, 100),
                glow_color=(255, 180, 50), glow_radius=10
            )

        # 상품 이미지 줌인
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 160,
                int(self.HEIGHT * 0.40)
            )
            ease = min(1.0, t / 0.7)
            self.draw_zoom_product(
                img, product_img, t,
                center_y=int(self.HEIGHT * 0.42),
                zoom_start=0.3, zoom_end=1.0, ease_t=ease
            )

        draw = ImageDraw.Draw(img)

        # 상품명 바운스
        if t > 0.5:
            self.draw_bounce_text(
                ImageDraw.Draw(img),
                int(self.HEIGHT * 0.68),
                self.get_product_name(), 50, t - 0.5,
                color=(255, 255, 255)
            )

        # 가격
        if t > 1.0:
            price_text = self.format_price(self.get_price())
            self.draw_glow_text(
                img, int(self.HEIGHT * 0.78), price_text, 48,
                color=(255, 150, 50),
                glow_color=(255, 100, 30), glow_radius=6
            )

        # "실제 구매자 후기" 안내
        if t > 1.5:
            fade = self.ease_out(min(1.0, (t - 1.5) / 0.5))
            font_hint = get_font(36)
            draw = ImageDraw.Draw(img)
            draw_text_centered(draw, int(self.HEIGHT * 0.88),
                              "📝 실제 구매자 후기 →", font_hint, self.WIDTH,
                              fill=(200, 200, int(255 * fade)))

        self.draw_sparkles(img, t, int(self.HEIGHT * 0.2), int(self.HEIGHT * 0.5))

    def _draw_review_section(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 2.5

        # 전환 플래시
        if dt < 0.15:
            self.draw_screen_flash(img, (0.15 - dt) / 0.15 * 0.3, (255, 255, 200))

        # 상단: 작은 상품 이미지 + 상품명
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                int(self.WIDTH * 0.3),
                int(self.HEIGHT * 0.12)
            )
            x = (self.WIDTH - product_img.width) // 2
            img.paste(product_img, (x, 30), product_img)

        draw = ImageDraw.Draw(img)

        # 별점 (작게)
        font_stars = get_font(36)
        draw_text_centered(draw, int(self.HEIGHT * 0.15),
                          "★★★★★ 5.0", font_stars, self.WIDTH,
                          fill=(255, 200, 0), shadow=False)

        # 리뷰 카드 (슬라이드업)
        card_ease = self.ease_out_back(min(1.0, dt / 0.5))
        review_y = int(self.HEIGHT * 0.22 + 50 * (1 - card_ease))
        review_h = int(self.HEIGHT * 0.50)

        bg_review = add_rounded_rectangle(
            img, 50, review_y, self.WIDTH - 100, review_h, 30,
            (255, 255, 255, int(240 * card_ease))
        )
        img.paste(bg_review)
        draw = ImageDraw.Draw(img)

        # 따옴표 장식 (큰 것)
        font_quote = get_font(100, bold=True)
        draw.text((70, review_y + 10), '"', font=font_quote,
                  fill=(220, 200, 150))

        # 리뷰 텍스트 (타자기 효과)
        review = self.get_review() or "정말 좋은 상품이에요! 품질이 뛰어나고 가격도 합리적입니다. 배송도 빠르고 포장도 꼼꼼합니다. 강력 추천합니다!"
        font_review = get_font(36)

        chars_per_sec = 12
        chars_to_show = int(chars_per_sec * max(0, dt - 0.5))
        visible_text = review[:min(len(review), chars_to_show)]

        if visible_text:
            lines = wrap_text(visible_text, font_review,
                            self.WIDTH - 180, draw)
            line_y = review_y + 80
            for line in lines[:8]:
                draw_text_centered(draw, line_y, line,
                                  font_review, self.WIDTH,
                                  fill=(40, 40, 40), shadow=False)
                line_y += 52

            # 커서 깜빡임
            if chars_to_show < len(review) and int(t * 3) % 2 == 0:
                cursor_x = self.WIDTH // 2 + len(lines[-1]) * 8 if lines else self.WIDTH // 2
                draw.rectangle(
                    [min(cursor_x, self.WIDTH - 60), line_y - 50,
                     min(cursor_x + 3, self.WIDTH - 57), line_y - 10],
                    fill=(100, 100, 100)
                )

        # 닫는 따옴표
        if chars_to_show >= len(review):
            draw.text((self.WIDTH - 140, review_y + review_h - 100),
                     '"', font=font_quote, fill=(220, 200, 150))

        # 하단: 가격 + 구매자 정보
        bottom_y = int(self.HEIGHT * 0.78)
        if dt > 0.5:
            font_buyer = get_font(30)
            draw_text_centered(draw, bottom_y, "— 실구매자 인증 리뷰 —",
                              font_buyer, self.WIDTH,
                              fill=(150, 150, 180))

        font_name = get_font(38, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.84),
                          self.get_product_name(), font_name, self.WIDTH)

        price_text = self.format_price(self.get_price())
        font_price = get_font(44, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.90),
                          price_text, font_price, self.WIDTH,
                          fill=(255, 100, 60))

    def _draw_purchase_section(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 7.0

        # 전환 플래시
        if dt < 0.2:
            self.draw_screen_flash(img, (0.2 - dt) / 0.2 * 0.4, (255, 200, 100))

        # 상품 이미지
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 200,
                int(self.HEIGHT * 0.28)
            )
            pulse = 1.0 + 0.02 * math.sin(dt * 2)
            w = int(product_img.width * pulse)
            h = int(product_img.height * pulse)
            product_img = product_img.resize((w, h), Image.LANCZOS)
            x = (self.WIDTH - w) // 2
            img.paste(product_img, (x, int(self.HEIGHT * 0.05)), product_img)

        draw = ImageDraw.Draw(img)

        # 별점 + 점수
        font_stars = get_font(50)
        draw_text_centered(draw, int(self.HEIGHT * 0.38),
                          "★★★★★", font_stars, self.WIDTH,
                          fill=(255, 200, 0), shadow=False)

        # 리뷰 요약 (한 줄)
        review = self.get_review() or "강력 추천!"
        short_review = review[:30] + ("..." if len(review) > 30 else "")
        font_review_sum = get_font(34)
        draw_text_centered(draw, int(self.HEIGHT * 0.46),
                          f'"{short_review}"', font_review_sum, self.WIDTH,
                          fill=(200, 200, 220))

        # 상품명
        self.draw_glow_text(img, int(self.HEIGHT * 0.54),
                           self.get_product_name(), 52,
                           color=(255, 255, 255),
                           glow_color=(200, 150, 255), glow_radius=8)

        # 가격 (글로우)
        price_text = self.format_price(self.get_price())
        self.draw_glow_text(img, int(self.HEIGHT * 0.63), price_text, 70,
                           color=(255, 80, 60),
                           glow_color=(255, 50, 30), glow_radius=10)

        # CTA 버튼 (펄스)
        draw = ImageDraw.Draw(img)
        pulse = 0.93 + 0.07 * math.sin(dt * 8)
        btn_w = int((self.WIDTH - 200) * pulse)
        btn_x = (self.WIDTH - btn_w) // 2
        btn_y = int(self.HEIGHT * 0.78)
        bg_btn = add_rounded_rectangle(
            img, btn_x, btn_y, btn_w, 110, 55,
            (255, 69, 58, int(220 + 35 * math.sin(dt * 6)))
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
                          "👆 후회 없는 선택!", font_hint, self.WIDTH,
                          fill=(200, 200, 255))

        # 제휴 링크
        self.draw_affiliate_bar(img, t, fade_start=7.0)

        # 컨페티
        self.draw_confetti(img, t, start_t=7.0)
        self.draw_sparkles(img, t)
