# Quickstart: UI Layout Dashboard

**Date**: 2026-01-06
**Feature**: 002-ui-layout-dashboard

This guide helps developers quickly understand and start working on the UI layout dashboard feature.

---

## Prerequisites

Ensure 001-core-accounting is implemented and working:

```bash
# Backend running
cd backend && uvicorn src.api.main:app --reload

# Frontend running
cd frontend && npm run dev

# PostgreSQL running with data
docker-compose up -d postgres
```

---

## Feature Overview

This feature adds:

1. **Dark sidebar navigation** with expandable account categories
2. **Dashboard homepage** with financial metrics and charts
3. **Account transaction view** when clicking an account

### Visual Reference

Mirauve Financial Dashboard (Dribbble shot 23051720):

- Dark sidebar (left)
- Card-based metrics (center)
- Donut chart for income/expense breakdown
- Bar charts for monthly trends

---

## Quick Implementation Guide

### Backend: New Files

```
backend/src/
├── api/routes/
│   └── dashboard.py          # NEW - 3 endpoints
└── services/
    └── dashboard_service.py  # NEW - aggregation logic
```

### Frontend: New Files

```
frontend/src/
├── app/
│   ├── layout.tsx            # MODIFY - wrap with sidebar
│   ├── page.tsx              # MODIFY - dashboard content
│   └── accounts/[id]/page.tsx # NEW - transaction view
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx       # NEW
│   │   └── SidebarItem.tsx   # NEW
│   └── dashboard/
│       ├── BalanceCard.tsx   # NEW
│       ├── IncomeExpenseChart.tsx # NEW
│       └── TrendChart.tsx    # NEW
└── lib/hooks/
    └── useDashboard.ts       # NEW
```

---

## Step-by-Step Development

### Step 1: Backend Dashboard Endpoint

```python
# backend/src/api/routes/dashboard.py
from fastapi import APIRouter, Depends
from ..deps import get_session
from ...services.dashboard_service import DashboardService

router = APIRouter(prefix="/ledgers/{ledger_id}", tags=["dashboard"])

@router.get("/dashboard")
def get_dashboard(ledger_id: UUID, session = Depends(get_session)):
    service = DashboardService()
    return service.get_dashboard_summary(ledger_id, session)
```

### Step 2: Frontend Sidebar Component

```tsx
// frontend/src/components/layout/Sidebar.tsx
export function Sidebar() {
  const { data: categories } = useSidebarAccounts();

  return (
    <aside className="w-64 bg-[#1a1a2e] text-white">
      <div className="p-4">
        <Logo />
      </div>
      {categories.map((category) => (
        <SidebarItem key={category.type} category={category} />
      ))}
    </aside>
  );
}
```

### Step 3: Dashboard Charts

```tsx
// frontend/src/components/dashboard/IncomeExpenseChart.tsx
import { DonutChart } from "@tremor/react";

export function IncomeExpenseChart({ income, expenses }) {
  const data = [
    { name: "Income", value: income },
    { name: "Expenses", value: expenses },
  ];

  return (
    <DonutChart
      data={data}
      category="value"
      index="name"
      colors={["emerald", "fuchsia"]}
    />
  );
}
```

---

## Key Design Decisions

| Decision         | Choice                | Rationale                            |
| ---------------- | --------------------- | ------------------------------------ |
| Charting library | Tremor                | Already in deps, Tailwind-native     |
| Sidebar state    | Session storage + URL | Persistent but not over-engineered   |
| Data fetching    | Dedicated endpoint    | Single API call, backend aggregation |
| Mobile sidebar   | Overlay drawer        | Standard responsive pattern          |

---

## Testing Checklist

Before implementation, write tests for:

- [ ] Dashboard service aggregation logic
- [ ] Empty state handling (no transactions)
- [ ] 6-month trend calculation with partial data
- [ ] Sidebar expand/collapse behavior
- [ ] Mobile responsive layout
- [ ] Account selection and URL sync

---

## API Quick Reference

```bash
# Get dashboard data
curl http://localhost:8000/api/v1/ledgers/{id}/dashboard

# Get accounts by category
curl http://localhost:8000/api/v1/ledgers/{id}/accounts/by-category

# Get account transactions
curl http://localhost:8000/api/v1/accounts/{id}/transactions?page=1
```

---

## Color Tokens

```css
/* Sidebar (dark theme) */
--sidebar-bg: #1a1a2e;
--sidebar-text: #e4e4e7;
--sidebar-hover: #2d2d44;

/* Chart colors */
--income: emerald-500;
--expense: fuchsia-500;
```

---

## Related Documentation

- [Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [API Contract](./contracts/dashboard_service.md)
- [Research](./research.md)
