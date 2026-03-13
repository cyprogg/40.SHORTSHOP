"""ShortShop - TTS 나레이션 생성기 (edge-tts 기반)"""
import asyncio
import tempfile
import os
from pathlib import Path

# 한국어 음성 목록
VOICES = {
    "female": "ko-KR-SunHiNeural",    # 여성 (밝고 또렷한)
    "male": "ko-KR-InJoonNeural",      # 남성
}

# 템플릿별 나레이션 스타일
TEMPLATE_NARRATION_STYLE = {
    "showcase": {"voice": "female", "rate": "+15%", "pitch": "+5Hz"},
    "price_drop": {"voice": "female", "rate": "+10%", "pitch": "+8Hz"},
    "flash_sale": {"voice": "female", "rate": "+20%", "pitch": "+10Hz"},
    "feature_highlight": {"voice": "female", "rate": "+10%", "pitch": "+3Hz"},
    "best_review": {"voice": "female", "rate": "+5%", "pitch": "+0Hz"},
}


def build_narration_script(product_data: dict) -> str:
    """상품 데이터로부터 나레이션 대본 생성"""
    parts = []

    name = product_data.get("name", "").strip()
    if name:
        parts.append(name + "!")

    desc = product_data.get("description", "").strip()
    if desc:
        parts.append(desc + ".")

    features = product_data.get("features", [])
    if features:
        feat_text = ", ".join(f[:30] for f in features[:5])
        parts.append(feat_text + ".")

    review = product_data.get("review", "").strip()
    if review:
        parts.append(review)

    cta = product_data.get("cta", "").strip()
    if cta:
        parts.append(cta)

    return " ".join(parts)


def generate_tts(product_data: dict, output_dir: str,
                 template_id: str = "showcase") -> str | None:
    """
    상품 데이터로 TTS 음성 파일 생성

    Args:
        product_data: 상품 정보 dict
        output_dir: 출력 디렉토리
        template_id: 템플릿 ID (스타일 결정)

    Returns:
        생성된 mp3 파일 경로 (실패시 None)
    """
    script = build_narration_script(product_data)
    if not script.strip():
        return None

    style = TEMPLATE_NARRATION_STYLE.get(template_id, TEMPLATE_NARRATION_STYLE["showcase"])
    voice = VOICES[style["voice"]]
    rate = style["rate"]
    pitch = style["pitch"]

    # 출력 파일 경로
    output_path = os.path.join(output_dir, "narration.mp3")

    try:
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(
                text=script,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
            await communicate.save(output_path)

        # 새 이벤트 루프에서 실행 (스레드 내에서 안전)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_generate())
        finally:
            loop.close()

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None

    except Exception as e:
        print(f"[TTS] 나레이션 생성 실패: {e}")
        return None
