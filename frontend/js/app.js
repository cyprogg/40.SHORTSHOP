/**
 * ShortShop - 프론트엔드 메인 로직
 */

// === 상태 관리 ===
const state = {
    uploadedImages: [],       // [{filename, path, previewUrl}]
    selectedTemplate: null,   // 템플릿 ID
    templates: [],            // 서버에서 로드한 템플릿 목록
    generating: false,
};

// === DOM 요소 ===
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    productName: () => $("#productName"),
    price: () => $("#price"),
    originalPrice: () => $("#originalPrice"),
    description: () => $("#description"),
    features: () => $("#features"),
    review: () => $("#review"),
    cta: () => $("#cta"),
    affiliateId: () => $("#affiliateId"),
    affiliateLink: () => $("#affiliateLink"),
    uploadArea: () => $("#uploadArea"),
    imageInput: () => $("#imageInput"),
    imagePreviewList: () => $("#imagePreviewList"),
    templateGrid: () => $("#templateGrid"),
    btnGenerate: () => $("#btnGenerate"),
    resultSection: () => $("#resultSection"),
    resultVideo: () => $("#resultVideo"),
    btnDownload: () => $("#btnDownload"),
    btnRetry: () => $("#btnRetry"),
    loadingOverlay: () => $("#loadingOverlay"),
};

// === 초기화 ===
document.addEventListener("DOMContentLoaded", async () => {
    await loadTemplates();
    setupUpload();
    setupGenerate();
    setupRetry();
    updateGenerateButton();
});

// === 템플릿 로드 ===
async function loadTemplates() {
    try {
        const res = await fetch("/api/templates");
        state.templates = await res.json();
        renderTemplates();
    } catch (e) {
        console.error("템플릿 로드 실패:", e);
    }
}

function renderTemplates() {
    const grid = dom.templateGrid();
    grid.innerHTML = "";

    state.templates.forEach((tpl) => {
        const card = document.createElement("div");
        card.className = "template-card";
        card.dataset.id = tpl.id;
        card.innerHTML = `
            <div class="template-icon">${tpl.icon}</div>
            <div class="template-name">${tpl.name}</div>
            <div class="template-desc">${tpl.description}</div>
            <div class="template-duration">${tpl.duration}초</div>
        `;
        card.addEventListener("click", () => selectTemplate(tpl.id));
        grid.appendChild(card);
    });
}

function selectTemplate(id) {
    state.selectedTemplate = id;
    $$(".template-card").forEach((card) => {
        card.classList.toggle("selected", card.dataset.id === id);
    });
    updateGenerateButton();
}

// === 이미지 업로드 ===
function setupUpload() {
    const area = dom.uploadArea();
    const input = dom.imageInput();

    area.addEventListener("click", () => input.click());

    area.addEventListener("dragover", (e) => {
        e.preventDefault();
        area.classList.add("dragover");
    });

    area.addEventListener("dragleave", () => {
        area.classList.remove("dragover");
    });

    area.addEventListener("drop", (e) => {
        e.preventDefault();
        area.classList.remove("dragover");
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    input.addEventListener("change", () => {
        handleFiles(input.files);
        input.value = "";
    });
}

async function handleFiles(files) {
    for (const file of files) {
        if (!file.type.startsWith("image/")) continue;
        await uploadImage(file);
    }
}

async function uploadImage(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "업로드 실패");
            return;
        }

        const data = await res.json();
        const previewUrl = URL.createObjectURL(file);

        state.uploadedImages.push({
            filename: data.filename,
            path: data.path,
            previewUrl,
        });

        renderImagePreviews();
        updateGenerateButton();
    } catch (e) {
        console.error("업로드 에러:", e);
        alert("이미지 업로드 중 오류가 발생했습니다.");
    }
}

function renderImagePreviews() {
    const list = dom.imagePreviewList();
    list.innerHTML = "";

    state.uploadedImages.forEach((img, idx) => {
        const item = document.createElement("div");
        item.className = "image-preview-item";
        item.innerHTML = `
            <img src="${img.previewUrl}" alt="상품 이미지">
            <button class="remove-btn" data-idx="${idx}">✕</button>
        `;
        item.querySelector(".remove-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            removeImage(idx);
        });
        list.appendChild(item);
    });
}

function removeImage(idx) {
    URL.revokeObjectURL(state.uploadedImages[idx].previewUrl);
    state.uploadedImages.splice(idx, 1);
    renderImagePreviews();
    updateGenerateButton();
}

// === 생성 버튼 상태 ===
function updateGenerateButton() {
    const btn = dom.btnGenerate();
    const name = dom.productName().value.trim();
    const price = dom.price().value.trim();
    const hasTemplate = !!state.selectedTemplate;
    const hasImage = state.uploadedImages.length > 0;

    btn.disabled = !(name && price && hasTemplate && hasImage) || state.generating;
}

// 입력 필드 변경 감지
document.addEventListener("input", updateGenerateButton);

// === 영상 생성 ===
function setupGenerate() {
    dom.btnGenerate().addEventListener("click", generateVideo);
}

async function generateVideo() {
    if (state.generating) return;
    state.generating = true;
    updateGenerateButton();
    showLoading(true);

    // 특징 파싱
    const featuresRaw = dom.features().value.trim();
    let featuresArr = [];
    if (featuresRaw) {
        featuresArr = featuresRaw
            .split(/[\n,]+/)
            .map((f) => f.trim())
            .filter(Boolean);
    }

    const imageFilenames = state.uploadedImages.map((img) => img.filename);

    const formData = new FormData();
    formData.append("template_id", state.selectedTemplate);
    formData.append("product_name", dom.productName().value.trim());
    formData.append("price", dom.price().value.trim());
    formData.append("original_price", dom.originalPrice().value.trim());
    formData.append("description", dom.description().value.trim());
    formData.append("features", JSON.stringify(featuresArr));
    formData.append("review", dom.review().value.trim());
    formData.append("cta", dom.cta().value.trim() || "지금 바로 구매하세요!");
    formData.append("affiliate_id", dom.affiliateId().value.trim());
    formData.append("affiliate_link", dom.affiliateLink().value.trim());
    formData.append("images", JSON.stringify(imageFilenames));

    try {
        const res = await fetch("/api/generate", {
            method: "POST",
            body: formData,
        });

        const resText = await res.text();
        if (!res.ok) {
            let msg = "생성 실패";
            try {
                const err = JSON.parse(resText);
                msg = err.detail || msg;
            } catch {
                msg = resText || msg;
            }
            throw new Error(msg);
        }

        const data = JSON.parse(resText);
        showResult(data.download_url, data.filename);
    } catch (e) {
        console.error("생성 에러:", e);
        alert("영상 생성 중 오류가 발생했습니다.\n" + e.message);
    } finally {
        state.generating = false;
        updateGenerateButton();
        showLoading(false);
    }
}

function showResult(downloadUrl, filename) {
    const section = dom.resultSection();
    const video = dom.resultVideo();
    const btnDl = dom.btnDownload();

    video.src = downloadUrl;
    btnDl.href = downloadUrl;
    btnDl.download = filename;

    section.style.display = "block";
    section.scrollIntoView({ behavior: "smooth" });
}

function showLoading(show) {
    dom.loadingOverlay().style.display = show ? "flex" : "none";
}

// === 다시 만들기 ===
function setupRetry() {
    dom.btnRetry().addEventListener("click", () => {
        dom.resultSection().style.display = "none";
        dom.resultVideo().src = "";
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
}
