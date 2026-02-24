import hashlib
import os
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import Session, col, select

from src.api.deps import get_session
from src.models.account import Account
from src.models.import_session import ImportSession, ImportStatus
from src.models.transaction import Transaction
from src.schemas.data_import import (
    BankConfig,
    ImportExecuteRequest,
    ImportJobStatus,
    ImportPreviewResponse,
    ImportResult,
    ImportType,
    ValidationError,
)
from src.services.csv_parser import BankStatementCsvParser, CreditCardCsvParser, MyAbCsvParser
from src.services.import_service import ImportService

router = APIRouter()


@router.post("/ledgers/{ledger_id}/import/preview", response_model=ImportPreviewResponse)
async def create_import_preview(
    ledger_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    import_type: Annotated[ImportType, Form(...)],
    session: Session = Depends(get_session),
    bank_code: Annotated[str | None, Form()] = None,
    reference_ledger_id: Annotated[uuid.UUID | None, Form()] = None,
) -> Any:
    """
    Parse CSV and generate import preview.
    """
    # 1. Validate file size (10MB limit)
    MAX_SIZE = 10 * 1024 * 1024

    # 2. Save file temporarily
    upload_dir = os.path.join("tmp", "imports")
    os.makedirs(upload_dir, exist_ok=True)

    session_id = uuid.uuid4()
    filename = file.filename or "import.csv"
    file_ext = os.path.splitext(filename)[1]
    save_path = os.path.join(upload_dir, f"{str(session_id)}{file_ext}")

    sha256 = hashlib.sha256()
    size = 0

    with open(save_path, "wb") as f:
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > MAX_SIZE:
                f.close()
                os.remove(save_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large (max 10MB)",
                )
            sha256.update(chunk)
            f.write(chunk)

    file_hash = sha256.hexdigest()

    # 3. Parse
    parsed_txs: list[Any] = []
    validation_errors: list[ValidationError] = []

    with open(save_path, "rb") as f:
        try:
            if import_type == ImportType.MYAB_CSV:
                parser_myab = MyAbCsvParser()
                parsed_txs, validation_errors = parser_myab.parse(f)
            elif import_type == ImportType.CREDIT_CARD:
                if not bank_code:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="bank_code is required for credit card import",
                    )
                parser_cc = CreditCardCsvParser(bank_code)
                parsed_txs, validation_errors = parser_cc.parse(f)
            elif import_type == ImportType.BANK_STATEMENT:
                if not bank_code:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="bank_code is required for bank statement import",
                    )
                parser_bs = BankStatementCsvParser(bank_code)
                parsed_txs, validation_errors = parser_bs.parse(f)
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Import type not supported yet",
                )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3b. LLM category enhancement (credit card and bank statement)
    if import_type in (ImportType.CREDIT_CARD, ImportType.BANK_STATEMENT) and parsed_txs:
        from src.models.account import AccountType as ModelAccountType  # noqa: PLC0415
        from src.services.llm_category_enhancer import LLMCategoryEnhancer  # noqa: PLC0415

        ledger_ids = [ledger_id]
        if reference_ledger_id:
            ledger_ids.append(reference_ledger_id)

        if import_type == ImportType.BANK_STATEMENT:
            expense_accounts_raw = session.exec(
                select(Account).where(
                    col(Account.ledger_id).in_(ledger_ids),
                    col(Account.type).in_([ModelAccountType.EXPENSE, ModelAccountType.INCOME]),
                )
            ).all()
        else:
            expense_accounts_raw = session.exec(
                select(Account).where(
                    col(Account.ledger_id).in_(ledger_ids),
                    Account.type == ModelAccountType.EXPENSE,
                )
            ).all()

        # Deduplicate: prefer current ledger's version when names clash
        seen_expense: set[str] = set()
        expense_accounts = []
        for acc in sorted(expense_accounts_raw, key=lambda a: a.ledger_id != ledger_id):
            if acc.name not in seen_expense:
                seen_expense.add(acc.name)
                expense_accounts.append(acc)

        enhancer = LLMCategoryEnhancer()
        parsed_txs = enhancer.enhance_batch(parsed_txs, expense_accounts)

    # 4. Generate Mappings
    ledger_ids_for_map = [ledger_id]
    if reference_ledger_id:
        ledger_ids_for_map.append(reference_ledger_id)

    all_accounts_raw = session.exec(
        select(Account).where(col(Account.ledger_id).in_(ledger_ids_for_map))
    ).all()

    # Deduplicate: prefer current ledger's version when names clash
    seen_all: set[str] = set()
    all_accounts: list[Account] = []
    for acc in sorted(all_accounts_raw, key=lambda a: a.ledger_id != ledger_id):
        if acc.name not in seen_all:
            seen_all.add(acc.name)
            all_accounts.append(acc)

    mapped_txs, mappings = ImportService.auto_map_accounts(parsed_txs, all_accounts)

    if len(mapped_txs) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction limit exceeded (max 2000)"
        )

    # 5. Find Duplicates
    dates = [tx.date for tx in mapped_txs if tx.date]
    duplicates = []
    min_date = None
    max_date = None

    if dates:
        min_date = min(dates)
        max_date = max(dates)
        # Fetch existing txs in range
        statement = select(Transaction).where(
            Transaction.ledger_id == ledger_id,
            Transaction.date >= min_date,
            Transaction.date <= max_date,
        )
        existing_txs = session.exec(statement).all()
        duplicates = ImportService.find_duplicates(mapped_txs, list(existing_txs))

    if not min_date:
        today = datetime.now().date()
        min_date = today
        max_date = today

    # 6. Create ImportSession
    import_session = ImportSession(
        id=session_id,
        ledger_id=ledger_id,
        import_type=import_type,
        source_filename=filename,
        source_file_hash=file_hash,
        bank_code=bank_code
        if import_type in (ImportType.CREDIT_CARD, ImportType.BANK_STATEMENT)
        else None,
        status=ImportStatus.PENDING,
        progress_total=len(mapped_txs),
        imported_count=0,
        skipped_count=0,
        error_count=0,
        created_accounts_count=0,
    )
    session.add(import_session)
    session.commit()

    # 7. Return Response
    return ImportPreviewResponse(
        session_id=session_id,
        total_count=len(mapped_txs),
        date_range={"start": min_date, "end": max_date},
        transactions=mapped_txs[:50],  # Return first 50 as sample
        duplicates=duplicates,
        account_mappings=mappings,
        validation_errors=validation_errors,
        is_valid=len(validation_errors) == 0,
    )


@router.post("/ledgers/{ledger_id}/import/execute", response_model=ImportResult)
async def execute_import(
    ledger_id: uuid.UUID,
    request: ImportExecuteRequest,
    session: Session = Depends(get_session),
) -> Any:
    """
    Execute the import based on a previous preview.
    """
    # 1. Fetch Session
    import_session = session.get(ImportSession, request.session_id)
    if not import_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import session not found"
        )

    if import_session.ledger_id != ledger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to this ledger"
        )

    if import_session.status != ImportStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not in PENDING state"
        )

    # 2. Load File & Re-parse
    upload_dir = os.path.join("tmp", "imports")
    # We used uuid.ext naming
    file_ext = os.path.splitext(import_session.source_filename)[1]
    save_path = os.path.join(upload_dir, f"{str(import_session.id)}{file_ext}")

    if not os.path.exists(save_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Preview expired or file missing"
        )

    try:
        parsed_txs: list[Any] = []
        with open(save_path, "rb") as f:
            if import_session.import_type == ImportType.MYAB_CSV:
                parser_myab = MyAbCsvParser()
                parsed_txs, _ = parser_myab.parse(f)
            elif import_session.import_type == ImportType.CREDIT_CARD:
                if not import_session.bank_code:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bank code not found in import session",
                    )
                parser_cc = CreditCardCsvParser(import_session.bank_code)
                parsed_txs, _ = parser_cc.parse(f)
            elif import_session.import_type == ImportType.BANK_STATEMENT:
                if not import_session.bank_code:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bank code not found in import session",
                    )
                parser_bs = BankStatementCsvParser(import_session.bank_code)
                parsed_txs, _ = parser_bs.parse(f)
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Import type not supported"
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-parse file: {e}",
        )

    # 3. Execute
    try:
        result = ImportService.execute_import(
            session=session,
            import_session=import_session,
            transactions=parsed_txs,
            mappings=request.account_mappings,
            skip_rows=request.skip_duplicate_rows,
            transaction_overrides=request.transaction_overrides or None,
        )
        session.commit()
        return result
    except ValueError as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        session.rollback()
        # Log error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/import/jobs/{_job_id}", response_model=ImportJobStatus)
async def get_import_job_status(_job_id: uuid.UUID) -> Any:
    """
    Get import job status.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/import/banks", response_model=dict[str, list[BankConfig]])
async def list_supported_banks(
    statement_type: str = Query(default="CREDIT_CARD"),
) -> Any:
    """
    List supported banks.

    Args:
        statement_type: "CREDIT_CARD" (default) or "BANK_STATEMENT"
    """
    if statement_type == "BANK_STATEMENT":
        from src.services.bank_configs import get_supported_bank_statement_banks  # noqa: PLC0415

        banks = get_supported_bank_statement_banks()
    else:
        from src.services.bank_configs import get_supported_banks  # noqa: PLC0415

        banks = get_supported_banks()

    return {"banks": [BankConfig(code=b.code, name=b.name, encoding=b.encoding) for b in banks]}


@router.get("/ledgers/{ledger_id}/import/history")
async def get_import_history(
    ledger_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> Any:
    """
    Get import history for a ledger.
    Returns paginated list of import sessions ordered by creation date (newest first).
    """
    from sqlmodel import func

    # Get total count
    count_statement = (
        select(func.count()).select_from(ImportSession).where(ImportSession.ledger_id == ledger_id)
    )
    total = session.exec(count_statement).one()

    # Get paginated items
    statement = (
        select(ImportSession)
        .where(ImportSession.ledger_id == ledger_id)
        .order_by(ImportSession.created_at.desc())  # type: ignore[attr-defined]
        .offset(offset)
        .limit(limit)
    )
    items = session.exec(statement).all()

    return {
        "items": [
            {
                "id": str(item.id),
                "import_type": item.import_type.value,
                "source_filename": item.source_filename,
                "status": item.status.value,
                "imported_count": item.imported_count,
                "skipped_count": item.skipped_count,
                "error_count": item.error_count,
                "created_accounts_count": item.created_accounts_count,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            }
            for item in items
        ],
        "total": total,
    }
