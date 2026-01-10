"""Category suggestion service for credit card transactions."""

from src.schemas.data_import import CategorySuggestion

# Category keywords mapping
# Keys are category names, values are lists of keywords to match
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "餐飲費": [
        "餐廳",
        "食品",
        "飲料",
        "咖啡",
        "麵包",
        "便當",
        "小吃",
        "星巴克",
        "starbucks",
        "麥當勞",
        "肯德基",
        "摩斯",
        "鼎泰豐",
        "火鍋",
        "燒肉",
        "壽司",
        "拉麵",
        "披薩",
        "美食",
        "早餐",
        "lunch",
        "dinner",
    ],
    "交通費": [
        "加油",
        "停車",
        "高鐵",
        "台鐵",
        "捷運",
        "uber",
        "計程車",
        "公車",
        "中油",
        "台亞",
        "全國加油",
        "機票",
        "航空",
        "taxi",
    ],
    "日用品": [
        "全聯",
        "家樂福",
        "好市多",
        "costco",
        "大潤發",
        "屈臣氏",
        "康是美",
        "7-11",
        "全家",
        "萊爾富",
        "超市",
        "量販",
        "日用",
    ],
    "網路購物": [
        "蝦皮",
        "shopee",
        "pchome",
        "momo",
        "博客來",
        "amazon",
        "淘寶",
        "天貓",
        "購物網",
        "線上購物",
    ],
    "娛樂費": [
        "電影",
        "ktv",
        "遊戲",
        "netflix",
        "spotify",
        "youtube",
        "disney",
        "影城",
        "威秀",
        "國賓",
        "秀泰",
        "演唱會",
        "展覽",
    ],
    "醫療費": [
        "診所",
        "醫院",
        "藥局",
        "藥房",
        "牙醫",
        "眼科",
        "健檢",
        "醫療",
        "保健",
    ],
    "教育費": [
        "書店",
        "補習",
        "課程",
        "學費",
        "誠品",
        "金石堂",
        "博客來",
        "線上課程",
        "udemy",
        "coursera",
    ],
}

# Default category when no match is found
DEFAULT_CATEGORY = "其他支出"


class CategorySuggester:
    """Suggest expense categories based on merchant/description keywords."""

    def __init__(self, custom_keywords: dict[str, list[str]] | None = None):
        """Initialize with optional custom keywords."""
        self.keywords = CATEGORY_KEYWORDS.copy()
        if custom_keywords:
            for category, words in custom_keywords.items():
                if category in self.keywords:
                    self.keywords[category].extend(words)
                else:
                    self.keywords[category] = words

    def suggest(self, description: str) -> CategorySuggestion:
        """
        Suggest a category for a transaction based on its description.

        Args:
            description: The merchant name or transaction description

        Returns:
            CategorySuggestion with suggested account name and confidence
        """
        if not description:
            return CategorySuggestion(
                suggested_account_name=DEFAULT_CATEGORY,
                confidence=0.0,
                matched_keyword=None,
            )

        description_lower = description.lower()

        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return CategorySuggestion(
                        suggested_account_name=category,
                        confidence=0.8,  # High confidence for keyword match
                        matched_keyword=keyword,
                    )

        # No match found - return default category
        return CategorySuggestion(
            suggested_account_name=DEFAULT_CATEGORY,
            confidence=0.3,  # Low confidence for default
            matched_keyword=None,
        )

    def suggest_batch(self, descriptions: list[str]) -> list[CategorySuggestion]:
        """
        Suggest categories for multiple descriptions.

        Args:
            descriptions: List of merchant names or transaction descriptions

        Returns:
            List of CategorySuggestion objects
        """
        return [self.suggest(desc) for desc in descriptions]
