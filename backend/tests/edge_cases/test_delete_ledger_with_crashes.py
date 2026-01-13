from datetime import datetime
from uuid import uuid4

from sqlmodel import Session, select

from src.models.audit_log import AuditAction, AuditLog
from src.models.import_session import ImportSession
from src.models.ledger import Ledger
from src.models.user import User
from src.schemas.data_import import ImportType as SchemaImportType
from src.schemas.ledger import LedgerCreate
from src.services.ledger_service import LedgerService


def test_delete_ledger_with_dependencies(session: Session):
    # 0. Create a user
    user = User(email="crash@test.com", display_name="Crash Test Helper")
    session.add(user)
    session.commit()
    user_id = user.id

    # 1. Create a ledger
    service = LedgerService(session)
    ledger = service.create_ledger(
        user_id, LedgerCreate(name="Crash Test Ledger", initial_balance=100)
    )

    # 2. Add an AuditLog entry linked to this ledger
    audit_log = AuditLog(
        ledger_id=ledger.id,
        entity_type="Account",
        entity_id=uuid4(),
        action=AuditAction.CREATE,
        timestamp=datetime.now(),
    )
    session.add(audit_log)

    # 3. Add an ImportSession linked to this ledger
    import_session = ImportSession(
        ledger_id=ledger.id,
        import_type=SchemaImportType.MYAB_CSV,
        source_filename="test.csv",
        source_file_hash="hash",
    )
    session.add(import_session)
    session.commit()

    # 4. Attempt to delete the ledger
    # This should succeed now, instead of raising IntegrityError
    result = service.delete_ledger(ledger.id, user_id)

    assert result is True

    # 5. Verify everything is gone
    assert session.get(Ledger, ledger.id) is None
    assert len(session.exec(select(AuditLog).where(AuditLog.ledger_id == ledger.id)).all()) == 0
    assert (
        len(session.exec(select(ImportSession).where(ImportSession.ledger_id == ledger.id)).all())
        == 0
    )
