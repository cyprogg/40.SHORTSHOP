"""ShortShop - 영상 생성 엔진"""
import uuid
import tempfile
import numpy as np
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLE_RATE = 44100


def generate_video(template_id: str, product_data: dict,
                   image_paths: list[str]) -> str:
    """
    숏폼 영상 생성

    Args:
        template_id: 템플릿 ID (showcase, price_drop, flash_sale, ...)
        product_data: 상품 정보 dict
        image_paths: 상품 이미지 경로 리스트

    Returns:
        생성된 영상 파일 경로
    """
    # 지연 임포트 (moviepy 로딩이 느림)
    from moviepy.editor import VideoClip, AudioClip, CompositeAudioClip, AudioFileClip
    from backend.templates import TEMPLATE_MAP
    from backend.utils.bgm_generator import generate_bgm, TEMPLATE_BGM_STYLE
    from backend.utils.tts_generator import generate_tts

    template_cls = TEMPLATE_MAP.get(template_id)
    if not template_cls:
        raise ValueError(f"알 수 없는 템플릿: {template_id}")

    template = template_cls(product_data, image_paths)

    # TTS 나레이션 생성
    tts_path = None
    tts_clip = None
    tmp_dir = tempfile.mkdtemp(prefix="shortshop_tts_")
    try:
        tts_path = generate_tts(product_data, tmp_dir, template_id)
    except Exception as e:
        print(f"[TTS] 나레이션 생성 스킵: {e}")

    # TTS가 영상보다 길면 영상 길이를 늘림 (+1초 여유)
    final_duration = template.duration
    if tts_path:
        try:
            from moviepy.editor import AudioFileClip as _AFC
            _probe = _AFC(tts_path)
            tts_dur = _probe.duration
            _probe.close()
            if tts_dur + 1.0 > final_duration:
                final_duration = tts_dur + 1.0
                print(f"[TTS] 영상 길이 확장: {template.duration}s → {final_duration:.1f}s (나레이션 {tts_dur:.1f}s)")
        except Exception:
            pass

    # 영상 클립 (확장된 duration 적용 — 마지막 프레임 유지)
    clip = VideoClip(template.make_frame, duration=final_duration)
    clip.fps = template.FPS

    # BGM 생성 (효과음 포함, 확장된 길이)
    bgm_style = TEMPLATE_BGM_STYLE.get(template_id, "upbeat")
    bgm_data = generate_bgm(final_duration, style=bgm_style,
                            sr=SAMPLE_RATE, template_id=template_id)

    # TTS가 있으면 BGM 볼륨 낮춤
    bgm_volume = 0.25 if tts_path else 1.0

    def make_audio_frame(t):
        """시간 t에서의 오디오 프레임 (스테레오)"""
        if isinstance(t, np.ndarray):
            indices = np.clip((t * SAMPLE_RATE).astype(int), 0, len(bgm_data) - 1)
            samples = bgm_data[indices] * bgm_volume
            return np.column_stack([samples, samples])
        else:
            idx = min(int(t * SAMPLE_RATE), len(bgm_data) - 1)
            val = bgm_data[idx] * bgm_volume
            return np.array([val, val])

    bgm_clip = AudioClip(make_audio_frame, duration=final_duration, fps=SAMPLE_RATE)
    bgm_clip.nchannels = 2

    # TTS+BGM 합성
    if tts_path:
        try:
            tts_clip = AudioFileClip(tts_path)
            # TTS 볼륨 조절 (나레이션이 잘 들리게)
            tts_clip = tts_clip.volumex(1.5)
            final_audio = CompositeAudioClip([bgm_clip, tts_clip])
            final_audio.fps = SAMPLE_RATE
        except Exception as e:
            print(f"[TTS] 오디오 합성 실패, BGM만 사용: {e}")
            final_audio = bgm_clip
    else:
        final_audio = bgm_clip

    clip = clip.set_audio(final_audio)

    # 출력 파일
    filename = f"shortshop_{template_id}_{uuid.uuid4().hex[:8]}.mp4"
    output_path = str(OUTPUT_DIR / filename)

    clip.write_videofile(
        output_path,
        fps=template.FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        logger="bar",
    )

    clip.close()
    if tts_clip:
        tts_clip.close()

    # 임시 TTS 파일 정리
    try:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    return output_path
