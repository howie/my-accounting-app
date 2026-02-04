import { createBrowserRouter } from 'react-router-dom';

import { RootLayout } from '@/components/layout/RootLayout';
import { SettingsLayout } from '@/components/layout/SettingsLayout';
import { ErrorBoundary } from '@/components/ErrorBoundary';

import Home from '@/pages/Home';
import SetupPage from '@/pages/SetupPage';
import LedgersPage from '@/pages/LedgersPage';
import LedgerDetailPage from '@/pages/LedgerDetailPage';
import ImportPage from '@/pages/ImportPage';
import ImportHistoryPage from '@/pages/ImportHistoryPage';
import AccountPage from '@/pages/AccountPage';
import ExportPage from '@/pages/ExportPage';
import BalanceSheetPage from '@/pages/reports/BalanceSheetPage';
import IncomeStatementPage from '@/pages/reports/IncomeStatementPage';
import SettingsPage from '@/pages/settings/SettingsPage';
import AccountManagementPage from '@/pages/settings/AccountManagementPage';
import TokensPage from '@/pages/settings/TokensPage';
import TagsSettingsPage from '@/pages/settings/TagsSettingsPage';
import RecurringSettingsPage from '@/pages/settings/RecurringSettingsPage';
import InstallmentsSettingsPage from '@/pages/settings/InstallmentsSettingsPage';

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      { path: '/', element: <Home /> },
      { path: '/setup', element: <SetupPage /> },
      { path: '/ledgers', element: <LedgersPage /> },
      { path: '/ledgers/:id', element: <LedgerDetailPage /> },
      { path: '/ledgers/:id/import', element: <ImportPage /> },
      { path: '/ledgers/:id/import/history', element: <ImportHistoryPage /> },
      { path: '/accounts/:id', element: <AccountPage /> },
      { path: '/export', element: <ExportPage /> },
      {
        path: '/reports',
        children: [
          { path: 'balance-sheet', element: <BalanceSheetPage /> },
          { path: 'income-statement', element: <IncomeStatementPage /> },
        ],
      },
      {
        path: '/settings',
        element: <SettingsLayout />,
        children: [
          { index: true, element: <SettingsPage /> },
          { path: 'accounts', element: <AccountManagementPage /> },
          { path: 'tokens', element: <TokensPage /> },
          { path: 'tags', element: <TagsSettingsPage /> },
          { path: 'recurring', element: <RecurringSettingsPage /> },
          { path: 'installments', element: <InstallmentsSettingsPage /> },
        ],
      },
    ],
  },
]);
