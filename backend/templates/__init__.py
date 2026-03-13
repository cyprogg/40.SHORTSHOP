"""ShortShop - 템플릿 패키지"""


def _get_template_map():
    """템플릿 클래스 맵 (지연 로드)"""
    from backend.templates.showcase import ShowcaseTemplate
    from backend.templates.price_drop import PriceDropTemplate
    from backend.templates.flash_sale import FlashSaleTemplate
    from backend.templates.feature_highlight import FeatureHighlightTemplate
    from backend.templates.best_review import BestReviewTemplate
    return {
        "showcase": ShowcaseTemplate,
        "price_drop": PriceDropTemplate,
        "flash_sale": FlashSaleTemplate,
        "feature_highlight": FeatureHighlightTemplate,
        "best_review": BestReviewTemplate,
    }


# 프록시: 최초 접근 시에만 실제 import
class _LazyTemplateMap:
    _map = None
    def _load(self):
        if self._map is None:
            self._map = _get_template_map()
    def get(self, key):
        self._load()
        return self._map.get(key)
    def keys(self):
        self._load()
        return self._map.keys()
    def __contains__(self, key):
        self._load()
        return key in self._map

TEMPLATE_MAP = _LazyTemplateMap()

TEMPLATE_INFO = {
    "showcase": {
        "id": "showcase",
        "name": "상품 쇼케이스",
        "description": "깔끔한 상품 소개 영상",
        "icon": "🛍️",
        "duration": 10,
    },
    "price_drop": {
        "id": "price_drop",
        "name": "가격 강조",
        "description": "할인가/특가 강조 영상",
        "icon": "💰",
        "duration": 8,
    },
    "flash_sale": {
        "id": "flash_sale",
        "name": "플래시 세일",
        "description": "긴급 타임세일 영상",
        "icon": "⚡",
        "duration": 7,
    },
    "feature_highlight": {
        "id": "feature_highlight",
        "name": "특징 하이라이트",
        "description": "상품 특징 순차 소개",
        "icon": "✨",
        "duration": 12,
    },
    "best_review": {
        "id": "best_review",
        "name": "베스트 리뷰",
        "description": "리뷰/후기 강조 영상",
        "icon": "🔥",
        "duration": 10,
    },
}
