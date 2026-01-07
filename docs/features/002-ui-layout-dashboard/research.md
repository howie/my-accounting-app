# Research: UI Layout Improvement with Sidebar Navigation and Dashboard

**Date**: 2026-01-06
**Feature**: 002-ui-layout-dashboard
**Source**: [spec.md](./spec.md), [plan.md](./plan.md)

## Research Summary

This document captures technology decisions and best practices research for the UI layout redesign feature.

---

## 1. Charting Library Selection

### Decision: Tremor

**Rationale**:
- Already included in 001-core-accounting dependencies
- Built specifically for React dashboards with Tailwind CSS
- Provides DonutChart and BarChart components out of the box
- Consistent styling with ShadcnUI design language
- TypeScript-first with excellent type definitions

**Alternatives Considered**:

| Library | Pros | Cons | Rejected Because |
|---------|------|------|------------------|
| Recharts | Popular, flexible | Requires more styling work | More setup needed for Mirauve style |
| Chart.js | Lightweight | Not React-native | Additional wrapper complexity |
| Victory | Powerful animations | Steeper learning curve | Over-engineered for our needs |
| D3.js | Ultimate flexibility | Low-level, verbose | Too complex for standard charts |

**Implementation Notes**:
```tsx
// Tremor components we'll use
import { DonutChart, BarChart, Card } from "@tremor/react";

// Color scheme aligned with Mirauve design
const colors = {
  income: "emerald",   // Green for positive
  expense: "fuchsia",  // Purple/pink for expenses
};
```

---

## 2. Sidebar Navigation Pattern

### Decision: Client-side state with URL sync

**Rationale**:
- Sidebar expand/collapse state persisted in session storage
- Selected account synced with URL for shareable links
- No server-side state needed for navigation

**Pattern**:
```tsx
// URL structure
/                       # Dashboard
/accounts/{id}          # Account transactions view

// Sidebar state
interface SidebarState {
  isCollapsed: boolean;           // Mobile toggle
  expandedCategories: string[];   // ASSET, LIABILITY, etc.
  selectedAccountId: string | null;
}
```

**Alternatives Considered**:

| Approach | Pros | Cons | Rejected Because |
|----------|------|------|------------------|
| Server-side state | Persistent across devices | Requires API calls | Overkill for UI preference |
| Context only | Simple | Lost on refresh | Poor UX |
| URL params only | Bookmarkable | Too many params | URL pollution |
| **Session + URL** | Balance of persistence and shareability | Slightly complex | ✓ Selected |

---

## 3. Responsive Layout Strategy

### Decision: Tailwind breakpoints with collapsible sidebar

**Rationale**:
- Mobile-first approach using Tailwind's responsive utilities
- Sidebar overlay on mobile (< 768px), persistent on desktop

**Breakpoints**:

| Breakpoint | Width | Sidebar Behavior | Layout |
|------------|-------|------------------|--------|
| `sm` | < 640px | Hidden (hamburger menu) | Single column |
| `md` | 640-768px | Overlay drawer | Single column + overlay |
| `lg` | 768-1024px | Collapsed (icons only) | Two column |
| `xl` | > 1024px | Full expanded | Two column |

**Implementation**:
```tsx
// Sidebar width tokens
const sidebarWidths = {
  collapsed: "w-16",   // 64px - icons only
  expanded: "w-64",    // 256px - full
};

// Main content margin
<main className="lg:ml-16 xl:ml-64 transition-all">
```

---

## 4. Dashboard Data Aggregation

### Decision: Dedicated backend endpoint with caching

**Rationale**:
- Single API call for all dashboard data reduces roundtrips
- Backend calculates aggregations for accuracy
- Response cached for performance (invalidated on transaction changes)

**API Design**:
```
GET /api/v1/ledgers/{ledger_id}/dashboard

Response:
{
  "total_assets": 21847.00,
  "current_month": {
    "income": 2992.00,
    "expenses": 1419.00
  },
  "trends": {
    "months": ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"],
    "income": [2500, 2800, 3100, 2900, 3200, 2992],
    "expenses": [1200, 1400, 1100, 1300, 1500, 1419]
  }
}
```

**Performance Considerations**:
- Cache dashboard response for 5 minutes
- Invalidate on any transaction CRUD
- Use indexed queries for date-range aggregations

---

## 5. Dark Sidebar Theming

### Decision: Tailwind dark variant with custom tokens

**Rationale**:
- Sidebar uses dark theme independent of main app theme
- Custom CSS variables for Mirauve color scheme
- Consistent with design reference

**Color Tokens**:
```css
/* Sidebar-specific colors (dark theme) */
:root {
  --sidebar-bg: #1a1a2e;           /* Dark navy */
  --sidebar-text: #e4e4e7;         /* Light gray */
  --sidebar-text-muted: #71717a;   /* Muted gray */
  --sidebar-accent: #4ade80;       /* Green accent */
  --sidebar-hover: #2d2d44;        /* Hover state */
  --sidebar-active: #3d3d5c;       /* Active/selected */
}
```

**Implementation**:
```tsx
<aside className="bg-[--sidebar-bg] text-[--sidebar-text]">
  {/* Dark sidebar content */}
</aside>
```

---

## 6. Account Grouping by Category

### Decision: Reuse existing AccountType enum

**Rationale**:
- 001-core-accounting defines AccountType: ASSET, LIABILITY, INCOME, EXPENSE
- Map to sidebar categories with display names

**Mapping**:

| AccountType | Sidebar Label | Icon | Notes |
|-------------|---------------|------|-------|
| ASSET | Assets | Wallet | Including Cash, Bank accounts |
| LIABILITY | Loans | CreditCard | Debts, loans payable |
| INCOME | Income | TrendingUp | Salary, revenue sources |
| EXPENSE | Expenses | Receipt | Spending categories |

**Implementation**:
```tsx
const categoryConfig = {
  ASSET: { label: "Assets", icon: Wallet },
  LIABILITY: { label: "Loans", icon: CreditCard },
  INCOME: { label: "Income", icon: TrendingUp },
  EXPENSE: { label: "Expenses", icon: Receipt },
};
```

---

## 7. Transaction List Performance

### Decision: Virtual scrolling with pagination fallback

**Rationale**:
- Most accounts have < 100 transactions (pagination sufficient)
- Virtual scrolling for accounts with > 500 transactions
- Server-side pagination with 50 items per page

**Implementation**:
```tsx
// API pagination
GET /api/v1/accounts/{id}/transactions?page=1&limit=50

// Frontend: react-window for virtual scrolling
import { FixedSizeList } from 'react-window';
```

---

## 8. Empty States Design

### Decision: Friendly illustrations with action prompts

**Rationale**:
- Empty states should guide users to next action
- Consistent with Mirauve friendly aesthetic

**Empty State Messages**:

| Context | Message | Action |
|---------|---------|--------|
| No accounts | "Start by creating your first account" | Create Account button |
| No transactions | "No transactions yet" | Add Transaction button |
| No data for trends | "Track more to see trends" | Shows available months only |

---

## References

1. Mirauve Dashboard Design: https://dribbble.com/shots/23051720-Mirauve-Financial-Management-Dashboard
2. Tremor Documentation: https://www.tremor.so/docs/getting-started/introduction
3. ShadcnUI Components: https://ui.shadcn.com/
4. Next.js App Router: https://nextjs.org/docs/app
5. Tailwind CSS Responsive: https://tailwindcss.com/docs/responsive-design
