"""ShortShop - FastAPI 메인 서버"""
import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.templates import TEMPLATE_INFO, TEMPLATE_MAP
from backend.video_generator import generate_video, OUTPUT_DIR

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("  ShortShop - 쇼핑 숏폼 자동생성기")
    print("  http://localhost:8001")
    print("=" * 50)
    yield


app = FastAPI(
    title="ShortShop",
    description="쇼핑 특화 숏폼 자동생성기",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def index():
    """메인 페이지"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/templates")
async def get_templates():
    """사용 가능한 템플릿 목록"""
    return JSONResponse(content=list(TEMPLATE_INFO.values()))


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """상품 이미지 업로드"""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(400, "지원하지 않는 이미지 형식입니다.")

    # 파일 크기 제한 (10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "파일 크기가 10MB를 초과합니다.")

    ext = Path(file.filename).suffix or ".jpg"
    # 안전한 파일명 생성
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    return {"filename": safe_filename, "path": str(file_path)}


@app.post("/api/generate")
async def generate(
    template_id: str = Form(...),
    product_name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(""),
    description: str = Form(""),
    features: str = Form("[]"),
    review: str = Form(""),
    cta: str = Form("지금 바로 구매하세요!"),
    affiliate_id: str = Form(""),
    affiliate_link: str = Form(""),
    images: str = Form("[]"),
):
    """숏폼 영상 생성"""
    if template_id not in TEMPLATE_MAP:
        raise HTTPException(400, f"알 수 없는 템플릿: {template_id}")

    # 상품 데이터 구성
    try:
        features_list = json.loads(features) if features else []
    except json.JSONDecodeError:
        features_list = [f.strip() for f in features.split(",") if f.strip()]

    try:
        image_list = json.loads(images) if images else []
    except json.JSONDecodeError:
        image_list = []

    product_data = {
        "name": product_name,
        "price": price,
        "original_price": original_price,
        "description": description,
        "features": features_list,
        "review": review,
        "cta": cta,
        "affiliate_id": affiliate_id,
        "affiliate_link": affiliate_link,
    }

    # 이미지 경로 확인
    image_paths = []
    for img_filename in image_list:
        img_path = UPLOAD_DIR / Path(img_filename).name
        if img_path.exists():
            image_paths.append(str(img_path))

    # 영상 생성 (비동기로 실행)
    loop = asyncio.get_event_loop()
    try:
        output_path = await loop.run_in_executor(
            None, generate_video, template_id, product_data, image_paths
        )
    except Exception as e:
        raise HTTPException(500, f"영상 생성 실패: {str(e)}")

    filename = Path(output_path).name
    return {
        "success": True,
        "filename": filename,
        "download_url": f"/api/download/{filename}",
    }


@app.get("/api/download/{filename}")
async def download(filename: str):
    """생성된 영상 다운로드"""
    # 경로 탐색 방지
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    return FileResponse(
        str(file_path),
        media_type="video/mp4",
        filename=safe_name,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "backend")],
    )
