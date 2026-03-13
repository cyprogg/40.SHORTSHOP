# ShortShop - 쇼핑 특화 숏폼 자동생성기

쇼핑/이커머스 상품을 위한 숏폼(Short-form) 영상 자동 생성 도구입니다.
TikTok, Instagram Reels, YouTube Shorts에 최적화된 9:16 세로형 영상을 자동으로 만들어줍니다.

## 주요 기능

- **상품 정보 입력**: 상품명, 가격, 설명, 특징, 이미지 업로드
- **5가지 숏폼 템플릿**:
  1. 🛍️ **상품 쇼케이스** - 깔끔한 상품 소개 영상
  2. 💰 **가격 강조** - 할인가/특가 강조 영상
  3. ⚡ **플래시 세일** - 긴급 타임세일 영상
  4. ✨ **특징 하이라이트** - 상품 특징 순차 소개
  5. 🔥 **베스트 리뷰** - 리뷰/후기 강조 영상
- **실시간 미리보기**: 생성 전 레이아웃 미리보기
- **다운로드**: MP4 형식으로 바로 다운로드

## 설치 방법

### 1. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. FFmpeg 설치

MoviePy가 내부적으로 FFmpeg를 사용합니다.

**Windows (winget):**
```bash
winget install FFmpeg
```

**Windows (choco):**
```bash
choco install ffmpeg
```

### 3. 실행
```bash
python backend/main.py
```

브라우저에서 http://localhost:8000 접속

## 프로젝트 구조

```
ShortShop/
├── backend/
│   ├── main.py              # FastAPI 서버 + 라우팅
│   ├── video_generator.py   # 핵심 영상 생성 엔진
│   ├── templates/           # 숏폼 템플릿 정의
│   │   ├── __init__.py
│   │   ├── base.py          # 템플릿 베이스 클래스
│   │   ├── showcase.py      # 상품 쇼케이스
│   │   ├── price_drop.py    # 가격 강조
│   │   ├── flash_sale.py    # 플래시 세일
│   │   ├── feature_highlight.py  # 특징 하이라이트
│   │   └── best_review.py   # 베스트 리뷰
│   └── utils/
│       ├── __init__.py
│       ├── image_processor.py  # 이미지 처리
│       └── text_renderer.py    # 텍스트 렌더링
├── frontend/
│   ├── index.html           # 메인 UI
│   ├── css/
│   │   └── style.css        # 스타일
│   └── js/
│       └── app.js           # 프론트엔드 로직
├── uploads/                 # 업로드된 이미지
├── output/                  # 생성된 영상
├── requirements.txt
└── README.md
```

## 기술 스택

- **Backend**: Python, FastAPI, MoviePy, Pillow
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Video**: FFmpeg (MoviePy 내장)
- **Format**: MP4 (H.264), 1080x1920 (9:16)
# 40.SHORTSHOP
