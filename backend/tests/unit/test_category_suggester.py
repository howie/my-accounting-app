"""T044: Unit test for category suggestion service"""

from src.services.category_suggester import CategorySuggester


class TestCategorySuggester:
    """Test category suggestion based on merchant/description keywords"""

    def test_suggest_food_category(self):
        """餐飲相關關鍵字應該建議餐飲費"""
        suggester = CategorySuggester()

        result = suggester.suggest("星巴克信義店")
        assert result.suggested_account_name == "餐飲費"
        assert result.confidence >= 0.7

        result = suggester.suggest("麥當勞台北車站")
        assert result.suggested_account_name == "餐飲費"

        result = suggester.suggest("鼎泰豐")
        assert result.suggested_account_name == "餐飲費"

    def test_suggest_transportation_category(self):
        """交通相關關鍵字應該建議交通費"""
        suggester = CategorySuggester()

        result = suggester.suggest("台灣高鐵")
        assert result.suggested_account_name == "交通費"

        result = suggester.suggest("中油加油站")
        assert result.suggested_account_name == "交通費"

        result = suggester.suggest("台北捷運")
        assert result.suggested_account_name == "交通費"

    def test_suggest_grocery_category(self):
        """日用品相關關鍵字應該建議日用品"""
        suggester = CategorySuggester()

        result = suggester.suggest("全聯福利中心")
        assert result.suggested_account_name == "日用品"

        result = suggester.suggest("家樂福內湖店")
        assert result.suggested_account_name == "日用品"

        result = suggester.suggest("屈臣氏")
        assert result.suggested_account_name == "日用品"

    def test_suggest_online_shopping_category(self):
        """網路購物相關關鍵字應該建議網路購物"""
        suggester = CategorySuggester()

        result = suggester.suggest("蝦皮購物")
        assert result.suggested_account_name == "網路購物"

        result = suggester.suggest("PCHOME")
        assert result.suggested_account_name == "網路購物"

        result = suggester.suggest("momo購物網")
        assert result.suggested_account_name == "網路購物"

    def test_suggest_entertainment_category(self):
        """娛樂相關關鍵字應該建議娛樂費"""
        suggester = CategorySuggester()

        result = suggester.suggest("NETFLIX")
        assert result.suggested_account_name == "娛樂費"

        result = suggester.suggest("威秀影城")
        assert result.suggested_account_name == "娛樂費"

        result = suggester.suggest("Spotify")
        assert result.suggested_account_name == "娛樂費"

    def test_suggest_medical_category(self):
        """醫療相關關鍵字應該建議醫療費"""
        suggester = CategorySuggester()

        result = suggester.suggest("台大醫院")
        assert result.suggested_account_name == "醫療費"

        result = suggester.suggest("大樹藥局")
        assert result.suggested_account_name == "醫療費"

        result = suggester.suggest("家庭診所")
        assert result.suggested_account_name == "醫療費"

    def test_suggest_education_category(self):
        """教育相關關鍵字應該建議教育費"""
        suggester = CategorySuggester()

        result = suggester.suggest("誠品書店")
        assert result.suggested_account_name == "教育費"

        result = suggester.suggest("金石堂書店")
        assert result.suggested_account_name == "教育費"

        result = suggester.suggest("補習班")
        assert result.suggested_account_name == "教育費"

    def test_suggest_default_category(self):
        """無法識別的商店應該建議其他支出"""
        suggester = CategorySuggester()

        result = suggester.suggest("不知名商店XYZ123")
        assert result.suggested_account_name == "其他支出"
        assert result.confidence < 0.5  # Low confidence for default

    def test_case_insensitive_matching(self):
        """關鍵字匹配應該不區分大小寫"""
        suggester = CategorySuggester()

        result = suggester.suggest("netflix")
        assert result.suggested_account_name == "娛樂費"

        result = suggester.suggest("STARBUCKS")
        assert result.suggested_account_name == "餐飲費"

    def test_matched_keyword_returned(self):
        """應該回傳匹配的關鍵字"""
        suggester = CategorySuggester()

        result = suggester.suggest("星巴克信義店")
        assert result.matched_keyword is not None
        assert "星巴克" in result.matched_keyword or "咖啡" in result.matched_keyword

    def test_suggest_batch(self):
        """批次處理多個商店名稱"""
        suggester = CategorySuggester()

        descriptions = ["星巴克", "高鐵", "全聯", "不明商店"]
        results = suggester.suggest_batch(descriptions)

        assert len(results) == 4
        assert results[0].suggested_account_name == "餐飲費"
        assert results[1].suggested_account_name == "交通費"
        assert results[2].suggested_account_name == "日用品"
        assert results[3].suggested_account_name == "其他支出"
