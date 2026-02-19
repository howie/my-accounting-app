"""Gmail credit card statement import API routes.

Feature 011: Gmail CC Statement Import
Handles OAuth2 connection, scanning, and statement import operations.
"""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from src.api.deps import get_session
from src.models.gmail_connection import GmailConnection, GmailConnectionStatus
from src.models.gmail_scan import DiscoveredStatement, ScanTriggerType, StatementScanJob
from src.schemas.gmail_import import (
    DiscoveredStatementResponse,
    GmailAuthUrlResponse,
    GmailConnectionResponse,
    GmailDisconnectResponse,
    ScanHistoryResponse,
    ScanJobResponse,
    StatementsListResponse,
    TriggerScanRequest,
)
from src.services.gmail_import_service import GmailImportError, GmailImportService
from src.services.gmail_service import GmailAuthError, GmailService, GmailServiceError

router = APIRouter()


def get_gmail_service() -> GmailService:
    """Dependency to get GmailService instance."""
    return GmailService()


# =============================================================================
# OAuth2 Connection Endpoints (US1)
# =============================================================================


@router.post("/gmail/auth/connect", response_model=GmailAuthUrlResponse)
async def initiate_gmail_connect(
    ledger_id: uuid.UUID = Query(..., description="Ledger ID to associate with Gmail connection"),
    gmail_service: GmailService = Depends(get_gmail_service),
) -> Any:
    """
    Initiate Gmail OAuth2 connection flow.

    Returns an authorization URL to redirect the user to Google's OAuth2 consent page.
    The ledger_id is encoded in the state parameter for retrieval after callback.
    """
    try:
        auth_url, _state = gmail_service.get_auth_url(ledger_id)
        return GmailAuthUrlResponse(auth_url=auth_url)
    except GmailServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {e}",
        )


@router.get("/gmail/auth/callback")
async def gmail_auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF validation"),
    error: str | None = Query(default=None, description="Error from Google if auth failed"),
    session: Session = Depends(get_session),
    gmail_service: GmailService = Depends(get_gmail_service),
) -> RedirectResponse:
    """
    Handle OAuth2 callback from Google.

    Exchanges the authorization code for access/refresh tokens,
    creates or updates the GmailConnection record, and redirects
    to the frontend Gmail settings page.
    """
    import os

    frontend_base_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Handle error from Google
    if error:
        error_url = f"{frontend_base_url}/gmail-import/settings?error={error}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

    try:
        # Exchange code for tokens
        (
            encrypted_access,
            encrypted_refresh,
            email_address,
            token_expiry,
            ledger_id,
        ) = gmail_service.handle_callback(code, state)

        # Get or create GmailConnection for this ledger
        ledger_uuid = uuid.UUID(ledger_id)

        existing = session.exec(
            select(GmailConnection).where(GmailConnection.ledger_id == ledger_uuid)
        ).first()

        if existing:
            # Update existing connection
            existing.email_address = email_address
            existing.encrypted_access_token = encrypted_access
            existing.encrypted_refresh_token = encrypted_refresh
            existing.token_expiry = token_expiry
            existing.status = GmailConnectionStatus.CONNECTED
            session.add(existing)
        else:
            # Create new connection
            connection = GmailConnection(
                ledger_id=ledger_uuid,
                email_address=email_address,
                encrypted_access_token=encrypted_access,
                encrypted_refresh_token=encrypted_refresh,
                token_expiry=token_expiry,
                status=GmailConnectionStatus.CONNECTED,
            )
            session.add(connection)

        session.commit()

        # Redirect to frontend with success
        success_url = (
            f"{frontend_base_url}/ledgers/{ledger_id}/gmail-import/settings?connected=true"
        )
        return RedirectResponse(url=success_url, status_code=status.HTTP_302_FOUND)

    except GmailAuthError as e:
        error_url = f"{frontend_base_url}/gmail-import/settings?error={str(e)}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)


@router.get("/gmail/connection", response_model=GmailConnectionResponse | None)
async def get_gmail_connection(
    ledger_id: uuid.UUID = Query(..., description="Ledger ID to check connection for"),
    session: Session = Depends(get_session),
) -> Any:
    """
    Get current Gmail connection status.

    Returns the connection details if connected, or null if not connected.
    """
    connection = session.exec(
        select(GmailConnection).where(GmailConnection.ledger_id == ledger_id)
    ).first()

    if not connection:
        return None

    return GmailConnectionResponse(
        id=connection.id,
        email_address=connection.email_address,
        status=connection.status,
        last_scan_at=connection.last_scan_at,
        scan_start_date=connection.scan_start_date,
        created_at=connection.created_at,
    )


@router.delete("/gmail/connection", response_model=GmailDisconnectResponse)
async def disconnect_gmail(
    ledger_id: uuid.UUID = Query(..., description="Ledger ID to disconnect"),
    session: Session = Depends(get_session),
    gmail_service: GmailService = Depends(get_gmail_service),
) -> Any:
    """
    Disconnect Gmail connection.

    Revokes OAuth2 tokens and removes the connection record.
    """
    connection = session.exec(
        select(GmailConnection).where(GmailConnection.ledger_id == ledger_id)
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Gmail connection found for this ledger",
        )

    # Try to revoke tokens (best effort, don't fail if this doesn't work)
    try:
        credentials = gmail_service.get_credentials(
            connection.encrypted_access_token,
            connection.encrypted_refresh_token,
            connection.token_expiry,
        )
        gmail_service.revoke_credentials(credentials)
    except Exception:
        # Revocation failure is not critical, continue with deletion
        pass

    # Delete the connection
    session.delete(connection)
    session.commit()

    return GmailDisconnectResponse(message="Gmail connection removed successfully")


# =============================================================================
# Bank Settings Endpoints (US4) - Stub implementations
# =============================================================================


@router.get("/gmail/banks")
async def list_supported_banks() -> Any:
    """
    List all supported banks for statement import.
    """
    from src.services.bank_parsers import get_bank_info

    banks = get_bank_info()
    return {"banks": banks}


@router.get("/gmail/banks/settings")
async def get_bank_settings(
    ledger_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),  # noqa: ARG001
) -> Any:
    """
    Get user's bank settings for a ledger.
    """
    # TODO: Implement in US4
    return {"settings": []}


@router.put("/gmail/banks/settings")
async def update_bank_settings(
    ledger_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),  # noqa: ARG001
) -> Any:
    """
    Update bank settings (enable/disable, password, account mapping).
    """
    # TODO: Implement in US4
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# =============================================================================
# Scan Endpoints (US2)
# =============================================================================


@router.post("/ledgers/{ledger_id}/gmail/scan", response_model=ScanJobResponse)
async def trigger_scan(
    ledger_id: uuid.UUID,
    body: TriggerScanRequest | None = None,
    session: Session = Depends(get_session),
) -> Any:
    """
    Trigger a manual scan for credit card statements.

    Searches Gmail for statement emails from enabled banks,
    downloads PDF attachments, and parses transactions.
    """
    import_service = GmailImportService(session)
    connection = import_service.get_connection(ledger_id)

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Gmail connection found. Connect Gmail first.",
        )

    if connection.status != GmailConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gmail connection is {connection.status.value}. Reconnect to scan.",
        )

    try:
        # Get user_id from ledger for bank settings lookup
        from src.models.ledger import Ledger

        ledger = session.exec(select(Ledger).where(Ledger.id == ledger_id)).first()
        if not ledger:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")

        job = import_service.execute_scan(
            ledger_id=ledger_id,
            user_id=ledger.user_id,
            trigger_type=ScanTriggerType.MANUAL,
        )

        return ScanJobResponse(
            id=job.id,
            trigger_type=job.trigger_type,
            status=job.status,
            banks_scanned=json.loads(job.banks_scanned),
            statements_found=job.statements_found,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
    except GmailImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/gmail/scan/{scan_job_id}", response_model=ScanJobResponse)
async def get_scan_status(
    scan_job_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> Any:
    """
    Get scan job status.
    """
    job = session.get(StatementScanJob, scan_job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")

    return ScanJobResponse(
        id=job.id,
        trigger_type=job.trigger_type,
        status=job.status,
        banks_scanned=json.loads(job.banks_scanned),
        statements_found=job.statements_found,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/gmail/scan/{scan_job_id}/statements", response_model=StatementsListResponse)
async def get_scan_statements(
    scan_job_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> Any:
    """
    Get statements discovered in a scan job.
    """
    job = session.get(StatementScanJob, scan_job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")

    statements = session.exec(
        select(DiscoveredStatement)
        .where(DiscoveredStatement.scan_job_id == scan_job_id)
        .order_by(DiscoveredStatement.email_date.desc())
    ).all()

    return StatementsListResponse(
        statements=[
            DiscoveredStatementResponse(
                id=s.id,
                bank_code=s.bank_code,
                bank_name=s.bank_name,
                billing_period_start=s.billing_period_start,
                billing_period_end=s.billing_period_end,
                email_subject=s.email_subject,
                email_date=s.email_date,
                pdf_filename=s.pdf_filename,
                parse_status=s.parse_status,
                parse_confidence=s.parse_confidence,
                transaction_count=s.transaction_count,
                total_amount=s.total_amount,
                import_status=s.import_status,
            )
            for s in statements
        ]
    )


# =============================================================================
# Preview & Import Endpoints (US2, US3)
# =============================================================================


@router.get("/gmail/statements/{statement_id}/preview", response_model=DiscoveredStatementResponse)
async def get_statement_preview(
    statement_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> Any:
    """
    Get preview of a discovered statement with parsed transactions.
    """
    statement = session.get(DiscoveredStatement, statement_id)
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")

    return DiscoveredStatementResponse(
        id=statement.id,
        bank_code=statement.bank_code,
        bank_name=statement.bank_name,
        billing_period_start=statement.billing_period_start,
        billing_period_end=statement.billing_period_end,
        email_subject=statement.email_subject,
        email_date=statement.email_date,
        pdf_filename=statement.pdf_filename,
        parse_status=statement.parse_status,
        parse_confidence=statement.parse_confidence,
        transaction_count=statement.transaction_count,
        total_amount=statement.total_amount,
        import_status=statement.import_status,
    )


@router.post("/ledgers/{ledger_id}/gmail/statements/{statement_id}/import")
async def import_statement(
    ledger_id: uuid.UUID,
    statement_id: uuid.UUID,
    session: Session = Depends(get_session),  # noqa: ARG001
) -> Any:
    """
    Import a statement's transactions into the ledger.
    """
    # TODO: Implement in US3
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# =============================================================================
# History Endpoints (US7)
# =============================================================================


@router.get("/gmail/scan/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    ledger_id: uuid.UUID = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> Any:
    """
    Get scan history for a ledger.
    """
    import_service = GmailImportService(session)
    jobs, total = import_service.get_scan_history(ledger_id, limit=limit, offset=offset)

    return ScanHistoryResponse(
        items=[
            ScanJobResponse(
                id=j.id,
                trigger_type=j.trigger_type,
                status=j.status,
                banks_scanned=json.loads(j.banks_scanned),
                statements_found=j.statements_found,
                error_message=j.error_message,
                started_at=j.started_at,
                completed_at=j.completed_at,
            )
            for j in jobs
        ],
        total=total,
    )


# =============================================================================
# Schedule Endpoints (US5) - Stub implementations
# =============================================================================


@router.get("/gmail/schedule")
async def get_schedule(
    ledger_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),  # noqa: ARG001
) -> Any:
    """
    Get current scan schedule settings.
    """
    # TODO: Implement in US5
    return {"frequency": None, "hour": None, "day_of_week": None, "next_scan_at": None}


@router.put("/gmail/schedule")
async def update_schedule(
    ledger_id: uuid.UUID = Query(...),
    session: Session = Depends(get_session),  # noqa: ARG001
) -> Any:
    """
    Update scan schedule settings.
    """
    # TODO: Implement in US5
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
