"""Gmail Import Service for credit card statement scanning and importing.

Orchestrates the full flow: Gmail search -> PDF download -> parse -> import.
"""

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, select

from src.models.gmail_connection import GmailConnection, GmailConnectionStatus
from src.models.gmail_scan import (
    DiscoveredStatement,
    ScanJobStatus,
    ScanTriggerType,
    StatementImportStatus,
    StatementParseStatus,
    StatementScanJob,
)
from src.models.user_bank_setting import UserBankSetting
from src.services.bank_parsers import get_all_bank_codes, get_bank_info, get_parser
from src.services.encryption import decrypt
from src.services.gmail_service import GmailService
from src.services.pdf_parser import PdfDecryptionError, PdfParseError, PdfParser


class GmailImportError(Exception):
    """Base error for Gmail import operations."""

    pass


class GmailImportService:
    """Service for scanning Gmail and importing credit card statements."""

    def __init__(self, session: Session):
        """Initialize with database session.

        Args:
            session: SQLModel database session.
        """
        self._session = session
        self._gmail_service = GmailService()

    def get_connection(self, ledger_id: uuid.UUID) -> GmailConnection | None:
        """Get Gmail connection for a ledger.

        Args:
            ledger_id: The ledger ID.

        Returns:
            GmailConnection if exists, None otherwise.
        """
        return self._session.exec(
            select(GmailConnection).where(GmailConnection.ledger_id == ledger_id)
        ).first()

    def get_enabled_banks(self, user_id: uuid.UUID) -> list[str]:
        """Get list of enabled bank codes for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of enabled bank codes, or all banks if none configured.
        """
        settings = self._session.exec(
            select(UserBankSetting).where(
                UserBankSetting.user_id == user_id,
                UserBankSetting.is_enabled == True,  # noqa: E712
            )
        ).all()

        if settings:
            return [s.bank_code for s in settings]

        # Default: return all supported banks
        return get_all_bank_codes()

    def get_bank_password(self, user_id: uuid.UUID, bank_code: str) -> str | None:
        """Get PDF password for a bank.

        Args:
            user_id: The user ID.
            bank_code: The bank code.

        Returns:
            Decrypted password if set, None otherwise.
        """
        setting = self._session.exec(
            select(UserBankSetting).where(
                UserBankSetting.user_id == user_id, UserBankSetting.bank_code == bank_code
            )
        ).first()

        if setting and setting.encrypted_pdf_password:
            return decrypt(setting.encrypted_pdf_password)

        return None

    def create_scan_job(
        self,
        gmail_connection_id: uuid.UUID,
        trigger_type: ScanTriggerType,
        bank_codes: list[str],
    ) -> StatementScanJob:
        """Create a new scan job.

        Args:
            gmail_connection_id: The Gmail connection ID.
            trigger_type: How the scan was triggered.
            bank_codes: List of bank codes to scan.

        Returns:
            The created scan job.
        """
        job = StatementScanJob(
            gmail_connection_id=gmail_connection_id,
            trigger_type=trigger_type,
            status=ScanJobStatus.PENDING,
            banks_scanned=json.dumps(bank_codes),
            statements_found=0,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def execute_scan(
        self,
        ledger_id: uuid.UUID,
        user_id: uuid.UUID,
        trigger_type: ScanTriggerType = ScanTriggerType.MANUAL,
    ) -> StatementScanJob:
        """Execute a full scan for credit card statements.

        Args:
            ledger_id: The ledger ID to scan for.
            user_id: The user ID for bank settings.
            trigger_type: How the scan was triggered.

        Returns:
            The completed scan job.

        Raises:
            GmailImportError: If scan fails.
        """
        # Get Gmail connection
        connection = self.get_connection(ledger_id)
        if not connection:
            raise GmailImportError("No Gmail connection found for this ledger")

        if connection.status != GmailConnectionStatus.CONNECTED:
            raise GmailImportError(f"Gmail connection is {connection.status.value}")

        # Get enabled banks
        bank_codes = self.get_enabled_banks(user_id)
        if not bank_codes:
            raise GmailImportError("No banks enabled for scanning")

        # Create scan job
        job = self.create_scan_job(connection.id, trigger_type, bank_codes)

        try:
            # Update job status
            job.status = ScanJobStatus.SCANNING
            job.started_at = datetime.now(UTC)
            self._session.add(job)
            self._session.commit()

            # Get Gmail API service
            credentials = self._gmail_service.get_credentials(
                connection.encrypted_access_token,
                connection.encrypted_refresh_token,
                connection.token_expiry,
            )
            service = self._gmail_service.build_service(credentials)

            # Scan each bank
            total_statements = 0
            for bank_code in bank_codes:
                try:
                    count = self._scan_bank(
                        service=service,
                        job=job,
                        user_id=user_id,
                        bank_code=bank_code,
                        scan_start_date=connection.scan_start_date,
                    )
                    total_statements += count
                except Exception as e:
                    # Log error but continue with other banks
                    print(f"Error scanning {bank_code}: {e}")

            # Update job completion
            job.status = ScanJobStatus.COMPLETED
            job.statements_found = total_statements
            job.completed_at = datetime.now(UTC)
            self._session.add(job)

            # Update connection last scan time
            connection.last_scan_at = datetime.now(UTC)
            self._session.add(connection)

            self._session.commit()
            self._session.refresh(job)

            return job

        except Exception as e:
            # Mark job as failed
            job.status = ScanJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(UTC)
            self._session.add(job)
            self._session.commit()
            raise GmailImportError(f"Scan failed: {e}")

    def _scan_bank(
        self,
        service,
        job: StatementScanJob,
        user_id: uuid.UUID,
        bank_code: str,
        scan_start_date,
    ) -> int:
        """Scan Gmail for statements from a specific bank.

        Args:
            service: Gmail API service.
            job: The scan job.
            user_id: The user ID for bank settings.
            bank_code: The bank code to scan.
            scan_start_date: Start date for scanning.

        Returns:
            Number of statements found.
        """
        parser = get_parser(bank_code)

        # Build search query
        query = parser.email_query
        if scan_start_date:
            query += f" after:{scan_start_date.strftime('%Y/%m/%d')}"

        # Search Gmail
        messages = self._gmail_service.search_messages(service, query, max_results=50)

        statements_found = 0
        for msg_info in messages:
            message_id = msg_info["id"]

            # Check if we've already processed this message
            existing = self._session.exec(
                select(DiscoveredStatement).where(
                    DiscoveredStatement.email_message_id == message_id
                )
            ).first()

            if existing:
                continue

            # Get full message
            message = self._gmail_service.get_message(service, message_id)

            # Extract email metadata
            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
            email_subject = headers.get("Subject", "")
            email_date_str = headers.get("Date", "")

            # Parse email date
            try:
                from email.utils import parsedate_to_datetime

                email_date = parsedate_to_datetime(email_date_str)
            except Exception:
                email_date = datetime.now(UTC)

            # Find PDF attachments
            attachments = self._find_pdf_attachments(message)

            for attachment in attachments:
                try:
                    # Create discovered statement record
                    statement = DiscoveredStatement(
                        scan_job_id=job.id,
                        bank_code=bank_code,
                        bank_name=parser.bank_name,
                        email_message_id=message_id,
                        email_subject=email_subject,
                        email_date=email_date,
                        pdf_attachment_id=attachment["id"],
                        pdf_filename=attachment["filename"],
                        parse_status=StatementParseStatus.PENDING,
                        import_status=StatementImportStatus.NOT_IMPORTED,
                    )
                    self._session.add(statement)
                    self._session.commit()
                    self._session.refresh(statement)

                    # Try to parse the statement
                    self._parse_statement(
                        service=service,
                        statement=statement,
                        message_id=message_id,
                        user_id=user_id,
                        parser=parser,
                    )

                    statements_found += 1

                except Exception as e:
                    print(f"Error processing attachment: {e}")

        return statements_found

    def _find_pdf_attachments(self, message: dict) -> list[dict]:
        """Find PDF attachments in a Gmail message.

        Args:
            message: Gmail message object.

        Returns:
            List of attachment info dicts with 'id' and 'filename'.
        """
        attachments = []

        def search_parts(parts):
            for part in parts:
                if part.get("filename", "").lower().endswith(".pdf"):
                    body = part.get("body", {})
                    attachment_id = body.get("attachmentId")
                    if attachment_id:
                        attachments.append({"id": attachment_id, "filename": part["filename"]})

                if "parts" in part:
                    search_parts(part["parts"])

        payload = message.get("payload", {})
        if "parts" in payload:
            search_parts(payload["parts"])

        return attachments

    def _parse_statement(
        self,
        service,
        statement: DiscoveredStatement,
        message_id: str,
        user_id: uuid.UUID,
        parser,
    ) -> None:
        """Parse a PDF statement and update the record.

        Args:
            service: Gmail API service.
            statement: The statement record to update.
            message_id: Gmail message ID.
            user_id: User ID for bank settings.
            parser: Bank parser instance.
        """
        try:
            # Download PDF
            pdf_data = self._gmail_service.get_attachment(
                service, message_id, statement.pdf_attachment_id
            )

            # Get password if needed
            password = self.get_bank_password(user_id, statement.bank_code)

            # Parse PDF
            pdf_parser = PdfParser(pdf_data)

            if pdf_parser.is_encrypted():
                if not password:
                    statement.parse_status = StatementParseStatus.PARSE_FAILED
                    statement.error_message = "PDF is encrypted but no password configured"
                    self._session.add(statement)
                    self._session.commit()
                    return

                try:
                    pdf_parser.decrypt(password)
                except PdfDecryptionError as e:
                    statement.parse_status = StatementParseStatus.PARSE_FAILED
                    statement.error_message = f"Failed to decrypt: {e}"
                    self._session.add(statement)
                    self._session.commit()
                    return

            # Extract text
            content = pdf_parser.extract_text()

            # Parse transactions
            transactions = parser.parse_statement(content)

            # Extract billing period
            start_date, end_date = parser.extract_billing_period(content)

            # Update statement record
            statement.billing_period_start = start_date
            statement.billing_period_end = end_date
            statement.parse_status = StatementParseStatus.PARSED
            statement.transaction_count = len(transactions)

            if transactions:
                statement.total_amount = sum(t.amount for t in transactions)
                statement.parse_confidence = sum(t.confidence for t in transactions) / len(
                    transactions
                )
            else:
                statement.total_amount = Decimal("0")
                statement.parse_confidence = 0.0

            self._session.add(statement)
            self._session.commit()

        except PdfParseError as e:
            statement.parse_status = StatementParseStatus.PARSE_FAILED
            statement.error_message = str(e)
            self._session.add(statement)
            self._session.commit()
        except Exception as e:
            statement.parse_status = StatementParseStatus.PARSE_FAILED
            statement.error_message = f"Unexpected error: {e}"
            self._session.add(statement)
            self._session.commit()

    def get_statement_preview(
        self, statement_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[DiscoveredStatement, list]:
        """Get a statement with parsed transactions for preview.

        Args:
            statement_id: The statement ID.
            user_id: The user ID for bank settings.

        Returns:
            Tuple of (statement, list of parsed transactions).

        Raises:
            GmailImportError: If statement not found or parsing fails.
        """
        statement = self._session.get(DiscoveredStatement, statement_id)
        if not statement:
            raise GmailImportError("Statement not found")

        if statement.parse_status == StatementParseStatus.PARSE_FAILED:
            raise GmailImportError(f"Statement parsing failed: {statement.error_message}")

        # Re-parse to get transactions (they're not stored in DB)
        # This requires access to the Gmail API again
        # In a production system, you might want to cache the parsed transactions

        return statement, []  # Placeholder - would need to re-fetch and parse

    def get_scan_history(
        self, ledger_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[StatementScanJob], int]:
        """Get scan history for a ledger.

        Args:
            ledger_id: The ledger ID.
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            Tuple of (list of scan jobs, total count).
        """
        connection = self.get_connection(ledger_id)
        if not connection:
            return [], 0

        # Get total count
        from sqlalchemy import func

        total = self._session.exec(
            select(func.count(StatementScanJob.id)).where(
                StatementScanJob.gmail_connection_id == connection.id
            )
        ).one()

        # Get paginated results
        jobs = self._session.exec(
            select(StatementScanJob)
            .where(StatementScanJob.gmail_connection_id == connection.id)
            .order_by(StatementScanJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return list(jobs), total

    def get_supported_banks(self) -> list[dict]:
        """Get list of all supported banks with info.

        Returns:
            List of bank info dicts.
        """
        return get_bank_info()
