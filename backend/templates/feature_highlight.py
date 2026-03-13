"""특징 하이라이트 템플릿 - 다이나믹 특징 소개"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
from backend.templates.base import BaseTemplate
from backend.utils.image_processor import (
    fit_image_in_box, create_gradient_background,
    add_rounded_rectangle, pil_to_numpy
)
from backend.utils.text_renderer import (
    get_font, draw_text_centered, draw_price_text
)


class FeatureHighlightTemplate(BaseTemplate):
    """
    특징 하이라이트: 특징을 하나씩 임팩트있게 소개
    구간: 상품소개(0-3s) → 특징들(3-9s) → CTA(9-12s)
    """

    FEATURE_COLORS = [
        (76, 200, 80),    # 초록
        (50, 150, 255),   # 파랑
        (255, 160, 0),    # 주황
        (180, 50, 220),   # 보라
        (255, 70, 70),    # 빨강
    ]

    FEATURE_EMOJIS = ["✅", "⭐", "💎", "🎯", "🔥"]

    def get_duration(self) -> float:
        return 12.0

    def make_frame(self, t: float) -> np.ndarray:
        bg = self.draw_moving_gradient_bg(t, (10, 10, 30), (30, 10, 50), (15, 20, 40))
        draw = ImageDraw.Draw(bg)

        if t < 3.0:
            self._draw_product_intro(draw, bg, t)
        elif t < 9.0:
            features = self.get_features()
            if not features:
                features = ["고품질 소재", "합리적 가격", "빠른 배송"]
            feature_duration = 6.0 / len(features)
            feature_idx = min(int((t - 3.0) / feature_duration), len(features) - 1)
            local_t = (t - 3.0) - feature_idx * feature_duration
            self._draw_feature(draw, bg, feature_idx, features[feature_idx],
                              local_t, feature_duration, t)
        else:
            self._draw_cta_screen(draw, bg, t)

        self.draw_animated_border(bg, t, color=(100, 180, 255), width=5)
        self.draw_vignette(bg, 0.3)
        return pil_to_numpy(bg)

    def _draw_product_intro(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        # 플래시 등장
        if t < 0.2:
            self.draw_screen_flash(img, (0.2 - t) / 0.2 * 0.5, (100, 150, 255))

        # 상품 이미지 (줌인)
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
                zoom_start=0.3, zoom_end=1.0, ease_t=ease
            )

        # 상품명 바운스
        if t > 0.3:
            self.draw_bounce_text(
                ImageDraw.Draw(img),
                int(self.HEIGHT * 0.56),
                self.get_product_name(), 60, t - 0.3,
                color=(255, 255, 255)
            )

        # "이런 점이 특별해요" 글로우
        if t > 1.2:
            fade = self.ease_out(min(1.0, (t - 1.2) / 0.6))
            self.draw_glow_text(
                img, int(self.HEIGHT * 0.66),
                "✨ 이런 점이 특별해요 ✨", 44,
                color=(200, 220, 255),
                glow_color=(100, 150, 255), glow_radius=8
            )

        # 가격
        if t > 1.5:
            price_text = self.format_price(self.get_price())
            price_ease = self.ease_out_elastic(min(1.0, (t - 1.5) / 0.7))
            y = int(self.HEIGHT * 0.78 - 20 * (1 - price_ease))
            self.draw_glow_text(
                img, y, price_text, 56,
                color=(255, 200, 80),
                glow_color=(255, 150, 50), glow_radius=8
            )

        # 특징 개수 미리보기
        if t > 2.0:
            features = self.get_features() or ["고품질 소재", "합리적 가격", "빠른 배송"]
            n = len(features)
            draw = ImageDraw.Draw(img)
            dots_y = int(self.HEIGHT * 0.88)
            dot_spacing = 50
            start_x = (self.WIDTH - (n - 1) * dot_spacing) // 2
            for i in range(n):
                color = self.FEATURE_COLORS[i % len(self.FEATURE_COLORS)]
                x = start_x + i * dot_spacing
                draw.ellipse([x - 10, dots_y - 10, x + 10, dots_y + 10],
                            fill=(*color, 200))

        self.draw_sparkles(img, t, int(self.HEIGHT * 0.2), int(self.HEIGHT * 0.5))

    def _draw_feature(self, draw: ImageDraw.Draw, img: Image.Image,
                      idx: int, feature: str, local_t: float,
                      duration: float, global_t: float):
        color = self.FEATURE_COLORS[idx % len(self.FEATURE_COLORS)]
        emoji = self.FEATURE_EMOJIS[idx % len(self.FEATURE_EMOJIS)]

        # 전환 플래시
        if local_t < 0.15:
            self.draw_screen_flash(img, (0.15 - local_t) / 0.15 * 0.4, color)

        # 큰 번호 (바운스)
        num_y = int(self.HEIGHT * 0.08)
        num_ease = self.ease_out_back(min(1.0, local_t / 0.4))
        font_num = get_font(max(1, int(100 * num_ease)), bold=True)
        if num_ease > 0.1:
            draw_text_centered(draw, num_y + int(30 * (1 - num_ease)),
                              f"{emoji} {idx + 1}", font_num, self.WIDTH,
                              fill=color)

        # 상품 이미지 (슬라이드 인)
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 260,
                int(self.HEIGHT * 0.28)
            )
            slide = self.ease_out(min(1.0, local_t / 0.5))
            x_start = -product_img.width
            x_end = (self.WIDTH - product_img.width) // 2
            x = int(x_start + (x_end - x_start) * slide)
            y = int(self.HEIGHT * 0.20)
            img.paste(product_img, (x, y), product_img)

        draw = ImageDraw.Draw(img)

        # 특징 카드 (아래에서 슬라이드업 + 바운스)
        card_ease = self.ease_out_back(min(1.0, max(0, (local_t - 0.2) / 0.5)))
        card_y_target = int(self.HEIGHT * 0.54)
        card_y = int(card_y_target + 100 * (1 - card_ease))
        card_h = 200

        if card_ease > 0.05:
            # 카드 배경 (컬러풀)
            bg_card = add_rounded_rectangle(
                img, 50, card_y, self.WIDTH - 100, card_h, 25,
                (*color, int(220 * card_ease))
            )
            img.paste(bg_card)
            draw = ImageDraw.Draw(img)

            # 특징 이모지 + 텍스트
            font_feature = get_font(48, bold=True)
            draw_text_centered(draw, card_y + 30,
                              f"{emoji} {feature}", font_feature, self.WIDTH,
                              fill=(255, 255, 255), shadow=False)

            # 체크마크 아이콘 라인
            font_check = get_font(36)
            draw_text_centered(draw, card_y + 110,
                              "━━━━━━━━ ✓ ━━━━━━━━",
                              font_check, self.WIDTH,
                              fill=(255, 255, 255, 150), shadow=False)

        # 하단 정보 바
        info_y = int(self.HEIGHT * 0.80)
        if local_t > 0.4:
            info_ease = self.ease_out(min(1.0, (local_t - 0.4) / 0.3))
            bg_info = add_rounded_rectangle(
                img, 40, info_y, self.WIDTH - 80, 120, 20,
                (0, 0, 0, int(160 * info_ease))
            )
            img.paste(bg_info)
            draw = ImageDraw.Draw(img)

            font_name = get_font(32, bold=True)
            draw_text_centered(draw, info_y + 15, self.get_product_name(),
                              font_name, self.WIDTH, fill=(200, 200, 200))

            price_text = self.format_price(self.get_price())
            font_price = get_font(42, bold=True)
            draw_text_centered(draw, info_y + 55, price_text,
                              font_price, self.WIDTH, fill=(255, 200, 50))

        # 진행 도트
        features = self.get_features() or ["고품질 소재", "합리적 가격", "빠른 배송"]
        n = len(features)
        dots_y = int(self.HEIGHT * 0.94)
        dot_spacing = 50
        start_x = (self.WIDTH - (n - 1) * dot_spacing) // 2
        for i in range(n):
            c = self.FEATURE_COLORS[i % len(self.FEATURE_COLORS)]
            x = start_x + i * dot_spacing
            if i == idx:
                # 현재 활성 (크게)
                draw.ellipse([x - 15, dots_y - 15, x + 15, dots_y + 15],
                            fill=(*c, 255))
            elif i < idx:
                # 완료 (체크)
                draw.ellipse([x - 10, dots_y - 10, x + 10, dots_y + 10],
                            fill=(*c, 200))
            else:
                # 미래 (작게)
                draw.ellipse([x - 8, dots_y - 8, x + 8, dots_y + 8],
                            fill=(100, 100, 100, 150))

        self.draw_particles(img, global_t, color_override=color, intensity=0.5)

    def _draw_cta_screen(self, draw: ImageDraw.Draw, img: Image.Image, t: float):
        dt = t - 9.0

        # 플래시
        if dt < 0.2:
            self.draw_screen_flash(img, (0.2 - dt) / 0.2 * 0.4, (100, 200, 255))

        # 상품 이미지
        if self.image_paths:
            product_img = fit_image_in_box(
                self.image_paths[0],
                self.WIDTH - 200,
                int(self.HEIGHT * 0.30)
            )
            # 슬로우 줌
            pulse = 1.0 + 0.02 * math.sin(dt * 2)
            w = int(product_img.width * pulse)
            h = int(product_img.height * pulse)
            product_img = product_img.resize((w, h), Image.LANCZOS)
            x = (self.WIDTH - w) // 2
            img.paste(product_img, (x, int(self.HEIGHT * 0.05)), product_img)

        draw = ImageDraw.Draw(img)

        # 상품명
        font_name = get_font(52, bold=True)
        draw_text_centered(draw, int(self.HEIGHT * 0.40),
                          self.get_product_name(), font_name, self.WIDTH)

        # 가격 글로우
        price_text = self.format_price(self.get_price())
        self.draw_glow_text(img, int(self.HEIGHT * 0.49), price_text, 72,
                           color=(255, 100, 80), glow_color=(255, 50, 30))

        # 특징 요약 (모든 특징 나열)
        features = self.get_features() or ["고품질", "합리적 가격", "빠른 배송"]
        draw = ImageDraw.Draw(img)
        y_start = int(self.HEIGHT * 0.60)
        for i, feat in enumerate(features[:4]):
            if dt > i * 0.2:
                feat_ease = self.ease_out(min(1.0, (dt - i * 0.2) / 0.3))
                color = self.FEATURE_COLORS[i % len(self.FEATURE_COLORS)]
                emoji = self.FEATURE_EMOJIS[i % len(self.FEATURE_EMOJIS)]
                font_feat = get_font(34, bold=True)
                y = y_start + i * 55 + int(15 * (1 - feat_ease))
                draw_text_centered(draw, y, f"{emoji} {feat}",
                                  font_feat, self.WIDTH, fill=color)

        # CTA 버튼
        pulse = 0.93 + 0.07 * math.sin(dt * 8)
        btn_w = int((self.WIDTH - 200) * pulse)
        btn_x = (self.WIDTH - btn_w) // 2
        btn_y = int(self.HEIGHT * 0.82)
        bg_btn = add_rounded_rectangle(
            img, btn_x, btn_y, btn_w, 110, 55,
            (50, 150, 255, 230)
        )
        img.paste(bg_btn)
        draw = ImageDraw.Draw(img)
        font_cta = get_font(44, bold=True)
        draw_text_centered(draw, btn_y + 25, self.get_cta(),
                          font_cta, self.WIDTH, fill=(255, 255, 255))

        # 제휴 링크
        self.draw_affiliate_bar(img, t, fade_start=9.0)

        # 컨페티
        self.draw_confetti(img, t, start_t=9.0)
        self.draw_sparkles(img, t)
