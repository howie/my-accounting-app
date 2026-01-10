import pytest
from fastapi.testclient import TestClient

from src.models.ledger import Ledger
from src.models.user import User
from src.schemas.data_import import ImportType


@pytest.fixture
def setup_user_and_ledger(session, sample_user_data, sample_ledger_data):
    user = User(**sample_user_data)
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(user_id=user.id, **sample_ledger_data)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return user, ledger


def test_import_flow(client: TestClient, setup_user_and_ledger):
    user, ledger = setup_user_and_ledger

    # 1. Preview
    csv_content = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-Food,,A-Cash,,100,Lunch,AB123
"""
    files = {"file": ("test.csv", csv_content, "text/csv")}
    preview_resp = client.post(
        f"/api/v1/ledgers/{ledger.id}/import/preview",
        files=files,
        data={"import_type": ImportType.MYAB_CSV.value},
    )
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    session_id = preview_data["session_id"]

    assert preview_data["is_valid"] is True
    assert len(preview_data["transactions"]) == 1

    # 2. Execute
    execute_data = {
        "session_id": session_id,
        "account_mappings": preview_data["account_mappings"],
        "skip_duplicate_rows": [],
    }

    exec_resp = client.post(f"/api/v1/ledgers/{ledger.id}/import/execute", json=execute_data)

    assert exec_resp.status_code == 200, exec_resp.text
    res = exec_resp.json()
    assert res["success"] is True
    assert res["imported_count"] == 1


# T046: Integration test for credit card import preview
# T047: Integration test for credit card import execute


def test_credit_card_import_preview(client: TestClient, setup_user_and_ledger):
    """T046: Test credit card CSV import preview with category suggestions"""
    user, ledger = setup_user_and_ledger

    csv_content = """交易日期,入帳日期,商店名稱,金額
2024/01/15,2024/01/16,星巴克信義店,150
2024/01/16,2024/01/17,全聯福利中心,520
2024/01/18,2024/01/19,台灣高鐵,1490
"""
    files = {"file": ("creditcard.csv", csv_content, "text/csv")}
    preview_resp = client.post(
        f"/api/v1/ledgers/{ledger.id}/import/preview",
        files=files,
        data={"import_type": ImportType.CREDIT_CARD.value, "bank_code": "CATHAY"},
    )

    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()

    assert preview_data["is_valid"] is True
    assert preview_data["total_count"] == 3

    # Check category suggestions
    txs = preview_data["transactions"]
    assert len(txs) == 3

    # 星巴克 should be suggested as 餐飲費
    tx1 = txs[0]
    assert tx1["description"] == "星巴克信義店"
    assert tx1["category_suggestion"] is not None
    assert tx1["category_suggestion"]["suggested_account_name"] == "餐飲費"

    # 全聯 should be suggested as 日用品
    tx2 = txs[1]
    assert tx2["category_suggestion"]["suggested_account_name"] == "日用品"

    # 高鐵 should be suggested as 交通費
    tx3 = txs[2]
    assert tx3["category_suggestion"]["suggested_account_name"] == "交通費"


def test_credit_card_import_execute(client: TestClient, setup_user_and_ledger):
    """T047: Test credit card CSV import execution"""
    user, ledger = setup_user_and_ledger

    # 1. Create a credit card account first

    # First, preview to get session
    csv_content = """交易日期,入帳日期,商店名稱,金額
2024/01/15,2024/01/16,星巴克信義店,150
"""
    files = {"file": ("creditcard.csv", csv_content, "text/csv")}
    preview_resp = client.post(
        f"/api/v1/ledgers/{ledger.id}/import/preview",
        files=files,
        data={"import_type": ImportType.CREDIT_CARD.value, "bank_code": "CATHAY"},
    )

    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    session_id = preview_data["session_id"]

    # 2. Execute import
    execute_data = {
        "session_id": session_id,
        "account_mappings": preview_data["account_mappings"],
        "skip_duplicate_rows": [],
    }

    exec_resp = client.post(f"/api/v1/ledgers/{ledger.id}/import/execute", json=execute_data)

    assert exec_resp.status_code == 200, exec_resp.text
    res = exec_resp.json()
    assert res["success"] is True
    assert res["imported_count"] == 1


def test_list_supported_banks(client: TestClient):
    """T055: Test GET /api/import/banks endpoint"""
    resp = client.get("/api/v1/import/banks")

    assert resp.status_code == 200
    data = resp.json()

    assert "banks" in data
    banks = data["banks"]
    assert len(banks) >= 5

    bank_codes = [b["code"] for b in banks]
    assert "CATHAY" in bank_codes
    assert "CTBC" in bank_codes
