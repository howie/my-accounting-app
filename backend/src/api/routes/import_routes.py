import hashlib
import os
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select

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
from src.services.csv_parser import CreditCardCsvParser, MyAbCsvParser
from src.services.import_service import ImportService

router = APIRouter()


@router.post("/ledgers/{ledger_id}/import/preview", response_model=ImportPreviewResponse)
async def create_import_preview(
    ledger_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    import_type: Annotated[ImportType, Form(...)],
    session: Session = Depends(get_session),
    bank_code: Annotated[str | None, Form()] = None,  # noqa: ARG001 - Reserved for credit card import
) -> Any:
    """
    Parse CSV and generate import preview.
    """
    # 1. Validate file size (10MB limit)
    # Note: parsing happens after save, checking size of stream is tricky without reading.
    # We check after reading or during read loop.
    MAX_SIZE = 10 * 1024 * 1024

    # 2. Save file temporarily
    upload_dir = os.path.join("tmp", "imports")
    os.makedirs(upload_dir, exist_ok=True)

    session_id = uuid.uuid4()
    # Sanitize filename or just use extension?
    # file.filename is optional, string|None
    filename = file.filename or "import.csv"
    file_ext = os.path.splitext(filename)[1]
    save_path = os.path.join(upload_dir, f"{str(session_id)}{file_ext}")

    sha256 = hashlib.sha256()
    size = 0

    with open(save_path, "wb") as f:
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > MAX_SIZE:
                # Clean up and raise
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
    parsed_txs: list[
        Any
    ] = []  # Use generic list to avoid union issues with different parsers for now
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
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Import type not supported yet",
                )
        except ValueError as e:
            # Fatal parsing error (e.g. file encoding, fundamental format)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 4. Generate Mappings
    existing_accounts = session.exec(select(Account).where(Account.ledger_id == ledger_id)).all()
    mapped_txs, mappings = ImportService.auto_map_accounts(parsed_txs, list(existing_accounts))

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
        bank_code=bank_code if import_type == ImportType.CREDIT_CARD else None,
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
async def list_supported_banks() -> Any:
    """
    List supported banks for credit card import.
    """
    from src.services.bank_configs import get_supported_banks

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
