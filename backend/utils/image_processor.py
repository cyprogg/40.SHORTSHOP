"""이미지 처리 유틸리티"""
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from pathlib import Path


# 숏폼 영상 해상도 (9:16 세로형)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def load_and_resize_image(image_path: str, target_width: int = VIDEO_WIDTH,
                          target_height: int = VIDEO_HEIGHT) -> Image.Image:
    """이미지 로드 후 영상 비율에 맞게 리사이즈 (커버 방식)"""
    img = Image.open(image_path).convert("RGBA")
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(target_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    # 중앙 크롭
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    img = img.crop((left, top, left + target_width, top + target_height))
    return img


def fit_image_in_box(image_path: str, box_width: int, box_height: int) -> Image.Image:
    """이미지를 박스 안에 맞추기 (contain 방식, 비율 유지)"""
    img = Image.open(image_path).convert("RGBA")
    img_ratio = img.width / img.height
    box_ratio = box_width / box_height

    if img_ratio > box_ratio:
        new_width = box_width
        new_height = int(box_width / img_ratio)
    else:
        new_height = box_height
        new_width = int(box_height * img_ratio)

    return img.resize((new_width, new_height), Image.LANCZOS)


def create_gradient_background(width: int, height: int,
                               color_top: tuple, color_bottom: tuple) -> Image.Image:
    """그라데이션 배경 생성 (벡터화)"""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    ratios = np.linspace(0, 1, height)
    for ch in range(3):
        arr[:, :, ch] = np.clip(
            color_top[ch] + (color_bottom[ch] - color_top[ch]) * ratios, 0, 255
        ).astype(np.uint8)[:, np.newaxis]
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def create_solid_background(width: int, height: int, color: tuple) -> Image.Image:
    """단색 배경 생성"""
    img = Image.new("RGBA", (width, height), color)
    return img


def create_blurred_background(image_path: str, width: int = VIDEO_WIDTH,
                              height: int = VIDEO_HEIGHT, blur_radius: int = 30) -> Image.Image:
    """이미지 블러 배경 생성"""
    img = load_and_resize_image(image_path, width, height)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)
    return img


def add_rounded_rectangle(img: Image.Image, x: int, y: int,
                          width: int, height: int, radius: int,
                          fill: tuple) -> Image.Image:
    """둥근 사각형 오버레이 추가"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        [(x, y), (x + width, y + height)],
        radius=radius,
        fill=fill
    )
    return Image.alpha_composite(img, overlay)


def add_overlay(base: Image.Image, overlay: Image.Image,
                position: tuple) -> Image.Image:
    """이미지 위에 오버레이 합성"""
    result = base.copy()
    result.paste(overlay, position, overlay)
    return result


def pil_to_numpy(img: Image.Image) -> np.ndarray:
    """PIL 이미지 -> numpy (RGB)"""
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return np.array(bg)
    return np.array(img.convert("RGB"))
