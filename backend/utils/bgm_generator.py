"""배경음악(BGM) + 사운드 이펙트 자동 생성 유틸리티

외부 음악 파일 없이 numpy로 쇼핑 숏폼에 적합한
업비트 배경음악 + 효과음을 프로그래밍 방식으로 생성합니다.
"""
import numpy as np

SAMPLE_RATE = 44100


def _sine(freq: float, duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _envelope(signal: np.ndarray, attack: float = 0.01,
              release: float = 0.05, sr: int = SAMPLE_RATE) -> np.ndarray:
    env = np.ones_like(signal)
    attack_samples = int(attack * sr)
    release_samples = int(release * sr)
    if attack_samples > 0:
        env[:attack_samples] = np.linspace(0, 1, attack_samples)
    if release_samples > 0:
        env[-release_samples:] = np.linspace(1, 0, release_samples)
    return signal * env


def _kick(duration: float = 0.15, sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq_sweep = 150 * np.exp(-t * 30) + 40
    phase = 2 * np.pi * np.cumsum(freq_sweep) / sr
    signal = np.sin(phase) * np.exp(-t * 15)
    return signal * 0.6


def _hihat(duration: float = 0.05, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(sr * duration)
    noise = np.random.randn(n)
    env = np.exp(-np.linspace(0, 20, n))
    return noise * env * 0.15


def _snare(duration: float = 0.1, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    tone = np.sin(2 * np.pi * 200 * t) * np.exp(-t * 30)
    noise = np.random.randn(n) * np.exp(-t * 20)
    return (tone * 0.3 + noise * 0.2) * 0.5


def _bass_note(freq: float, duration: float = 0.2,
               sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    return _envelope(signal, attack=0.005, release=0.05) * 0.25


def _pad_chord(freqs: list, duration: float = 1.0,
               sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.zeros_like(t)
    for f in freqs:
        signal += np.sin(2 * np.pi * f * t)
    signal /= len(freqs)
    return _envelope(signal, attack=0.1, release=0.2) * 0.12


# ---- 사운드 이펙트 ----

def _whoosh(duration: float = 0.3, sr: int = SAMPLE_RATE) -> np.ndarray:
    """슈웅~ 스와이프 효과음"""
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    noise = np.random.randn(n)
    # 밴드패스 느낌: 주파수가 올라갔다 내려감
    freq = 500 + 3000 * np.sin(np.pi * t / duration) ** 2
    mod = np.sin(2 * np.pi * np.cumsum(freq) / sr)
    env = np.sin(np.pi * t / duration)  # 볼록한 엔벨로프
    return noise * mod * env * 0.25


def _impact(duration: float = 0.2, sr: int = SAMPLE_RATE) -> np.ndarray:
    """쿵! 임팩트 효과음"""
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    # 저주파 펀치
    low = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 20)
    # 노이즈 어택
    noise = np.random.randn(n) * np.exp(-t * 40)
    return (low * 0.5 + noise * 0.3) * 0.6


def _ding(freq: float = 1200, duration: float = 0.4,
          sr: int = SAMPLE_RATE) -> np.ndarray:
    """딩! 알림 효과음"""
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    signal = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    env = np.exp(-t * 8)
    return signal * env * 0.3


def _rise(duration: float = 0.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """상승 효과음 (기대감)"""
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = 200 + 1500 * (t / duration) ** 2
    signal = np.sin(2 * np.pi * np.cumsum(freq) / sr)
    env = np.linspace(0.1, 0.4, n)
    return signal * env


def _ta_da(duration: float = 0.6, sr: int = SAMPLE_RATE) -> np.ndarray:
    """짜잔! 결과 공개 효과음"""
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    # 두 음 연속
    half = n // 2
    note1 = np.sin(2 * np.pi * 523.25 * t[:half]) * np.exp(-t[:half] * 6)  # C5
    note2 = np.sin(2 * np.pi * 783.99 * t[:half]) * np.exp(-t[:half] * 5)  # G5
    signal = np.zeros(n)
    signal[:half] = note1 * 0.3
    signal[half:] = note2[:n - half] * 0.35
    return signal


def _place(target: np.ndarray, source: np.ndarray, offset: int):
    end = min(offset + len(source), len(target))
    length = end - offset
    if length > 0 and offset >= 0:
        target[offset:end] += source[:length]


# 템플릿별 효과음 타이밍 (초 단위)
TEMPLATE_SFX_TIMING = {
    "showcase": [
        (0.0, "impact"),    # 인트로
        (1.5, "whoosh"),    # 상품 등장
        (5.0, "whoosh"),    # 정보 슬라이드
        (8.0, "ta_da"),     # CTA
    ],
    "price_drop": [
        (0.0, "impact"),    # 등장
        (2.0, "rise"),      # 원가 표시
        (3.5, "impact"),    # 가격 드롭!
        (3.7, "ding"),      # 딩!
        (5.5, "ta_da"),     # 최종 결과
    ],
    "flash_sale": [
        (0.0, "impact"),    # 경고
        (0.3, "ding"),      # 플래시
        (1.5, "whoosh"),    # 상품 등장
        (5.0, "rise"),      # 카운트다운
    ],
    "feature_highlight": [
        (0.0, "whoosh"),    # 인트로
        (3.0, "ding"),      # 특징1
        (5.0, "ding"),      # 특징2
        (7.0, "ding"),      # 특징3
        (9.0, "ta_da"),     # CTA
    ],
    "best_review": [
        (0.0, "impact"),    # 등장
        (2.5, "whoosh"),    # 리뷰 전환
        (7.0, "ta_da"),     # 구매 유도
    ],
}


def generate_bgm(duration: float, style: str = "upbeat",
                 sr: int = SAMPLE_RATE, template_id: str = None) -> np.ndarray:
    """
    배경음악 + 효과음 생성

    Args:
        duration: 음악 길이(초)
        style: 스타일 ("upbeat", "urgent", "calm")
        sr: 샘플레이트
        template_id: 효과음 타이밍용 템플릿 ID

    Returns:
        numpy array (samples,) float64, range [-1, 1]
    """
    total_samples = int(sr * duration)
    audio = np.zeros(total_samples)

    if style == "urgent":
        bpm = 140
    elif style == "calm":
        bpm = 100
    else:
        bpm = 120

    beat_duration = 60.0 / bpm
    beat_samples = int(beat_duration * sr)

    chord_progressions = {
        "upbeat": [
            [261.6, 329.6, 392.0],
            [220.0, 277.2, 329.6],
            [174.6, 220.0, 261.6],
            [196.0, 246.9, 293.7],
        ],
        "urgent": [
            [261.6, 311.1, 392.0],
            [207.7, 261.6, 311.1],
            [155.6, 196.0, 233.1],
            [233.1, 277.2, 349.2],
        ],
        "calm": [
            [261.6, 329.6, 392.0],
            [220.0, 261.6, 329.6],
            [174.6, 220.0, 261.6],
            [196.0, 246.9, 293.7],
        ],
    }

    bass_notes = {
        "upbeat": [130.8, 110.0, 87.3, 98.0],
        "urgent": [130.8, 103.8, 77.8, 116.5],
        "calm": [130.8, 110.0, 87.3, 98.0],
    }

    chords = chord_progressions.get(style, chord_progressions["upbeat"])
    basses = bass_notes.get(style, bass_notes["upbeat"])

    num_beats = int(duration / beat_duration) + 1

    for i in range(num_beats):
        pos = i * beat_samples
        if pos >= total_samples:
            break

        chord_idx = (i // 4) % len(chords)

        _place(audio, _kick(sr=sr), pos)
        _place(audio, _hihat(sr=sr), pos)
        _place(audio, _hihat(sr=sr), pos + beat_samples // 2)

        if i % 4 in (1, 3):
            _place(audio, _snare(sr=sr), pos)

        bass_freq = basses[chord_idx]
        _place(audio, _bass_note(bass_freq, beat_duration * 0.8, sr), pos)

        if i % 4 == 0:
            pad = _pad_chord(chords[chord_idx], beat_duration * 4, sr)
            _place(audio, pad, pos)

    # urgent 스타일 라이저
    if style == "urgent" and duration > 2:
        riser_len = min(2.0, duration * 0.3)
        riser_samples = int(riser_len * sr)
        t = np.linspace(0, riser_len, riser_samples, endpoint=False)
        riser = np.sin(2 * np.pi * (200 + 800 * (t / riser_len) ** 2) * t)
        riser *= np.linspace(0, 0.15, riser_samples)
        start = total_samples - riser_samples
        if start > 0:
            _place(audio, riser, start)

    # 효과음 믹싱
    sfx_layer = np.zeros(total_samples)
    sfx_map = {
        "whoosh": _whoosh,
        "impact": _impact,
        "ding": _ding,
        "rise": _rise,
        "ta_da": _ta_da,
    }
    if template_id and template_id in TEMPLATE_SFX_TIMING:
        for time_sec, sfx_name in TEMPLATE_SFX_TIMING[template_id]:
            if sfx_name in sfx_map:
                sfx = sfx_map[sfx_name](sr=sr)
                pos = int(time_sec * sr)
                _place(sfx_layer, sfx, pos)

    # BGM + 효과음 합성
    audio = audio * 0.7 + sfx_layer * 1.0

    # 페이드 인/아웃
    fade_in = int(0.2 * sr)
    fade_out = int(0.5 * sr)
    if fade_in < total_samples:
        audio[:fade_in] *= np.linspace(0, 1, fade_in)
    if fade_out < total_samples:
        audio[-fade_out:] *= np.linspace(1, 0, fade_out)

    # 클리핑 방지
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.85

    return audio


# 템플릿별 BGM 스타일 매핑
TEMPLATE_BGM_STYLE = {
    "showcase": "upbeat",
    "price_drop": "upbeat",
    "flash_sale": "urgent",
    "feature_highlight": "upbeat",
    "best_review": "calm",
}
