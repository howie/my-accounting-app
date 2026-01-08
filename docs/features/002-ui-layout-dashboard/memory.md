# Feature 002: UI Layout Dashboard - Session Memory

**Last Updated**: 2026-01-07
**Status**: Complete - Tree Structure Implementation Done

## Context

實現一個類似 MyAB 的 UI 佈局，包含左側深色側邊欄和右側 Dashboard。

## Current Session Progress

### Completed Tasks

- [x] Phase 1-6: 所有基礎實現完成
- [x] Backend DashboardService 和 API routes
- [x] Frontend Dashboard 組件 (BalanceCard, IncomeExpenseChart, TrendChart, DashboardGrid)
- [x] Frontend Sidebar 組件 (Sidebar, SidebarItem, AppShell)
- [x] Account transactions page (`/accounts/[id]`)
- [x] Mobile responsive hamburger menu
- [x] i18n translations (common.previous, common.next)
- [x] Route conflict fix (dashboard routes before accounts)

### Issues Found During Testing

#### Issue 1: 舊版畫面問題 (FIXED)

- **問題**: 訪問 `/ledgers/{id}` 顯示舊版頁面，重新整理才跳轉到新版
- **原因**: `/ledgers/[id]/page.tsx` 設置 currentLedger 後沒有自動跳轉
- **修復**: 在 `useEffect` 中加入 `router.push('/')`
- **檔案**: `frontend/src/app/ledgers/[id]/page.tsx` (已修改)

#### Issue 2: 側邊欄沒有樹狀結構 (FIXED)

- **問題**: 側邊欄帳號顯示為平面列表，沒有顯示父子關係
- **修復**: Backend 返回樹狀結構，Frontend 遞迴渲染並根據 depth 縮排

## Files Modified (Uncommitted)

```
modified:   backend/src/services/dashboard_service.py
modified:   frontend/src/app/ledgers/[id]/page.tsx
modified:   frontend/src/types/dashboard.ts
```

## Remaining Work for Tree Structure

### 1. Backend (DONE)

`backend/src/services/dashboard_service.py`:

- [x] `get_accounts_by_category()` 已改為返回樹狀結構
- [x] 新增 `_build_account_tree()` 方法

### 2. Frontend Types (DONE)

`frontend/src/types/dashboard.ts`:

- [x] `SidebarAccountItem` 已加入 `parent_id`, `depth`, `children`
- [x] `AccountsByCategoryResponse` 已更新
- [x] `transformAccount()` 遞迴轉換函數已加入

### 3. Frontend Hook (DONE)

`frontend/src/lib/hooks/useSidebarAccounts.ts`:

- [x] 更新 `transformResponse()` 使用新的樹狀結構
- [x] 新增 `transformAccount()` 遞迴轉換函數

### 4. Frontend SidebarItem (DONE)

`frontend/src/components/layout/SidebarItem.tsx`:

- [x] `AccountLink` 組件根據 `depth` 增加縮排
- [x] 遞迴渲染 `children`

## API Response Example (After Fix)

```json
{
  "categories": [
    {
      "type": "ASSET",
      "accounts": [
        {
          "id": "xxx",
          "name": "銀行",
          "balance": 0,
          "parent_id": null,
          "depth": 1,
          "children": [
            {
              "id": "yyy",
              "name": "華南銀行",
              "balance": 0,
              "parent_id": "xxx",
              "depth": 2,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

## Next Steps

1. 測試樹狀結構顯示
2. 提交所有修改

## Commands to Test

```bash
# Start backend
cd backend && source .venv/bin/activate && uvicorn src.main:app --reload

# Start frontend
cd frontend && npm run dev

# Test API
curl -s "http://localhost:8000/api/v1/ledgers/{ledger_id}/accounts/by-category" | python3 -m json.tool
```

## Git Status

Branch: `002-ui-layout-dashboard`
Last commit: `d3af90e` - fix(i18n): add missing common.previous and common.next translations
