"""텍스트 렌더링 유틸리티"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

# 시스템 폰트 경로
SYSTEM_FONT_DIRS = [
    "C:/Windows/Fonts",
    "/usr/share/fonts",
    "/System/Library/Fonts",
]

# 선호 한글 폰트 목록 (우선순위)
PREFERRED_FONTS = [
    "malgunbd.ttf",    # 맑은 고딕 Bold
    "malgun.ttf",      # 맑은 고딕
    "NanumGothicBold.ttf",
    "NanumGothic.ttf",
    "gulim.ttc",
    "batang.ttc",
]

PREFERRED_BOLD_FONTS = [
    "malgunbd.ttf",
    "NanumGothicExtraBold.ttf",
    "NanumGothicBold.ttf",
    "malgun.ttf",
]


def find_font(bold: bool = False) -> str:
    """사용 가능한 한글 폰트 경로 찾기"""
    font_list = PREFERRED_BOLD_FONTS if bold else PREFERRED_FONTS
    for font_dir in SYSTEM_FONT_DIRS:
        if not os.path.isdir(font_dir):
            continue
        for font_name in font_list:
            font_path = os.path.join(font_dir, font_name)
            if os.path.isfile(font_path):
                return font_path
    # 폴백: 기본 폰트
    return None


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """폰트 객체 가져오기"""
    size = max(1, int(size))
    font_path = find_font(bold)
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def draw_text_with_shadow(draw: ImageDraw.Draw, position: tuple, text: str,
                          font: ImageFont.FreeTypeFont,
                          fill: tuple = (255, 255, 255),
                          shadow_color: tuple = (0, 0, 0, 128),
                          shadow_offset: int = 3):
    """그림자 있는 텍스트 그리기"""
    x, y = position
    # 그림자
    draw.text((x + shadow_offset, y + shadow_offset), text,
              font=font, fill=shadow_color)
    # 본문
    draw.text((x, y), text, font=font, fill=fill)


def draw_text_centered(draw: ImageDraw.Draw, y: int, text: str,
                       font: ImageFont.FreeTypeFont,
                       canvas_width: int,
                       fill: tuple = (255, 255, 255),
                       shadow: bool = True):
    """가운데 정렬 텍스트"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas_width - text_width) // 2
    if shadow:
        draw_text_with_shadow(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]  # 텍스트 높이 반환


def draw_price_text(draw: ImageDraw.Draw, y: int, price: str,
                    canvas_width: int, font_size: int = 80,
                    color: tuple = (255, 69, 58)):
    """가격 텍스트 (크고 굵게)"""
    font = get_font(font_size, bold=True)
    return draw_text_centered(draw, y, price, font, canvas_width, fill=color)


def draw_strikethrough_price(draw: ImageDraw.Draw, y: int, price: str,
                             canvas_width: int, font_size: int = 40):
    """취소선 가격 (원가)"""
    font = get_font(font_size, bold=False)
    color = (180, 180, 180)
    bbox = draw.textbbox((0, 0), price, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (canvas_width - text_width) // 2
    draw.text((x, y), price, font=font, fill=color)
    # 취소선
    line_y = y + text_height // 2
    draw.line([(x - 5, line_y), (x + text_width + 5, line_y)],
              fill=color, width=3)
    return text_height


def draw_badge(img: Image.Image, text: str, position: tuple = (40, 40),
               bg_color: tuple = (255, 69, 58, 230),
               text_color: tuple = (255, 255, 255),
               font_size: int = 36) -> Image.Image:
    """배지/라벨 그리기"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = get_font(font_size, bold=True)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    padding = 16
    x, y = position

    draw.rounded_rectangle(
        [(x, y), (x + text_w + padding * 2, y + text_h + padding * 2)],
        radius=12,
        fill=bg_color
    )
    draw.text((x + padding, y + padding), text, font=font, fill=text_color)

    return Image.alpha_composite(img, overlay)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int,
              draw: ImageDraw.Draw) -> list:
    """텍스트 줄바꿈"""
    words = list(text)  # 한글은 글자 단위로
    lines = []
    current = ""

    for char in words:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = char

    if current:
        lines.append(current)
    return lines
