"""Reports API routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response, StreamingResponse

from src.api.deps import get_export_service, get_report_service
from src.schemas.report import BalanceSheet, IncomeStatement
from src.services.export_service import ExportFormat, ExportService
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/balance-sheet",
    response_model=BalanceSheet,
    status_code=status.HTTP_200_OK,
    summary="Get Balance Sheet",
)
async def get_balance_sheet(
    ledger_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    date: Annotated[date, Query(description="The date for the snapshot (YYYY-MM-DD)")],
) -> BalanceSheet:
    """Get Balance Sheet for a specific date."""
    return await report_service.get_balance_sheet(ledger_id=ledger_id, as_of_date=date)


@router.get(
    "/balance-sheet/export",
    summary="Export Balance Sheet",
)
async def export_balance_sheet(
    ledger_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
    date: Annotated[date, Query(description="The date for the snapshot (YYYY-MM-DD)")],
    format: Annotated[ExportFormat, Query(description="Export format (csv or html)")],
) -> Response:
    """Export Balance Sheet."""
    report = await report_service.get_balance_sheet(ledger_id=ledger_id, as_of_date=date)

    if format == ExportFormat.CSV:
        content_generator = export_service.generate_balance_sheet_csv(report)
        return StreamingResponse(
            content_generator,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=balance_sheet_{date}.csv"},
        )
    else:  # HTML
        html_content = export_service.generate_balance_sheet_html(report)
        return Response(content=html_content, media_type="text/html")


@router.get(
    "/income-statement",
    response_model=IncomeStatement,
    status_code=status.HTTP_200_OK,
    summary="Get Income Statement",
)
async def get_income_statement(
    ledger_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    start_date: Annotated[date, Query(description="Start date (inclusive)")],
    end_date: Annotated[date, Query(description="End date (inclusive)")],
) -> IncomeStatement:
    """Get Income Statement for a specific period."""
    return await report_service.get_income_statement(
        ledger_id=ledger_id, start_date=start_date, end_date=end_date
    )


@router.get(
    "/income-statement/export",
    summary="Export Income Statement",
)
async def export_income_statement(
    ledger_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
    start_date: Annotated[date, Query(description="Start date (inclusive)")],
    end_date: Annotated[date, Query(description="End date (inclusive)")],
    format: Annotated[ExportFormat, Query(description="Export format (csv or html)")],
) -> Response:
    """Export Income Statement."""
    report = await report_service.get_income_statement(
        ledger_id=ledger_id, start_date=start_date, end_date=end_date
    )

    if format == ExportFormat.CSV:
        content_generator = export_service.generate_income_statement_csv(report)
        return StreamingResponse(
            content_generator,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=income_statement_{start_date}_{end_date}.csv"
            },
        )
    else:  # HTML
        html_content = export_service.generate_income_statement_html(report)
        return Response(content=html_content, media_type="text/html")
