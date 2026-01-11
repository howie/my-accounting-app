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


def test_import_atomic_rollback_on_invalid_mapping(
    client: TestClient, session, setup_user_and_ledger
):
    """T018: Test atomic rollback when import fails due to invalid account mapping.

    Verifies that if import fails mid-way, all changes are rolled back:
    - No transactions should be created
    - No accounts should be created
    - Import session should remain in PENDING or be marked FAILED
    """
    import uuid

    from sqlmodel import select

    from src.models.account import Account
    from src.models.import_session import ImportSession, ImportStatus
    from src.models.transaction import Transaction

    user, ledger = setup_user_and_ledger

    # 1. Create preview with valid CSV
    csv_content = """日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-Food,,A-Cash,,100,Lunch,AB123
2024/01/02,支出,E-Transport,,A-Cash,,50,Bus,AB124
"""
    files = {"file": ("test.csv", csv_content, "text/csv")}
    preview_resp = client.post(
        f"/api/v1/ledgers/{ledger.id}/import/preview",
        files=files,
        data={"import_type": ImportType.MYAB_CSV.value},
    )
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    session_id_str = preview_data["session_id"]
    session_id = uuid.UUID(session_id_str)

    # Count existing transactions and accounts before attempt
    tx_count_before = len(
        session.exec(select(Transaction).where(Transaction.ledger_id == ledger.id)).all()
    )
    acc_count_before = len(
        session.exec(select(Account).where(Account.ledger_id == ledger.id)).all()
    )

    # 2. Execute with intentionally broken mappings (missing required account mapping)
    # Remove one of the required mappings to cause a failure
    broken_mappings = [
        m
        for m in preview_data["account_mappings"]
        if m["csv_account_name"] != "A-Cash"  # Remove the Cash mapping
    ]

    execute_data = {
        "session_id": session_id_str,
        "account_mappings": broken_mappings,
        "skip_duplicate_rows": [],
    }

    exec_resp = client.post(f"/api/v1/ledgers/{ledger.id}/import/execute", json=execute_data)

    # 3. Verify failure
    assert exec_resp.status_code in [400, 500]  # Should fail due to missing mapping

    # 4. Verify rollback - no new transactions or accounts should exist
    session.expire_all()  # Clear cache to get fresh data

    tx_count_after = len(
        session.exec(select(Transaction).where(Transaction.ledger_id == ledger.id)).all()
    )
    acc_count_after = len(session.exec(select(Account).where(Account.ledger_id == ledger.id)).all())

    assert tx_count_after == tx_count_before, "Transactions should be rolled back"
    assert acc_count_after == acc_count_before, "Accounts should be rolled back"

    # 5. Verify import session status
    import_session = session.get(ImportSession, session_id)
    assert import_session is not None
    # Session should either still be PENDING (not executed) or marked as FAILED
    assert import_session.status in [ImportStatus.PENDING, ImportStatus.FAILED]


def test_import_history(client: TestClient, _session, setup_user_and_ledger):
    """T068: Test GET /api/ledgers/{id}/import/history endpoint."""
    _user, ledger = setup_user_and_ledger

    # 1. Create and execute an import to have some history
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

    # Execute the import
    execute_data = {
        "session_id": preview_data["session_id"],
        "account_mappings": preview_data["account_mappings"],
        "skip_duplicate_rows": [],
    }
    exec_resp = client.post(f"/api/v1/ledgers/{ledger.id}/import/execute", json=execute_data)
    assert exec_resp.status_code == 200

    # 2. Get import history
    history_resp = client.get(f"/api/v1/ledgers/{ledger.id}/import/history")
    assert history_resp.status_code == 200
    history_data = history_resp.json()

    # 3. Verify history structure
    assert "items" in history_data
    assert "total" in history_data
    assert history_data["total"] >= 1

    # 4. Verify the most recent import is in the list
    items = history_data["items"]
    assert len(items) >= 1

    # Find the import we just did
    found = False
    for item in items:
        if item["id"] == preview_data["session_id"]:
            found = True
            assert item["import_type"] == "MYAB_CSV"
            assert item["status"] == "COMPLETED"
            assert item["imported_count"] == 1
            assert item["source_filename"] == "test.csv"
            break

    assert found, "Recently completed import should appear in history"


def test_import_history_pagination(client: TestClient, _session, setup_user_and_ledger):
    """Test import history pagination."""
    _user, ledger = setup_user_and_ledger

    # Create multiple import sessions
    for i in range(3):
        csv_content = f"""日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/{i + 1:02d},支出,E-Food,,A-Cash,,{100 + i},Item{i},
"""
        files = {"file": (f"test{i}.csv", csv_content, "text/csv")}
        preview_resp = client.post(
            f"/api/v1/ledgers/{ledger.id}/import/preview",
            files=files,
            data={"import_type": ImportType.MYAB_CSV.value},
        )
        assert preview_resp.status_code == 200

    # Get first page with limit 2
    resp1 = client.get(f"/api/v1/ledgers/{ledger.id}/import/history?limit=2&offset=0")
    assert resp1.status_code == 200
    data1 = resp1.json()

    assert len(data1["items"]) == 2
    assert data1["total"] >= 3

    # Get second page
    resp2 = client.get(f"/api/v1/ledgers/{ledger.id}/import/history?limit=2&offset=2")
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert len(data2["items"]) >= 1
    # Ensure no overlap
    ids1 = {item["id"] for item in data1["items"]}
    ids2 = {item["id"] for item in data2["items"]}
    assert ids1.isdisjoint(ids2), "Pagination pages should not overlap"
