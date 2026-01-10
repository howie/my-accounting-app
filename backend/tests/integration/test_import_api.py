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
