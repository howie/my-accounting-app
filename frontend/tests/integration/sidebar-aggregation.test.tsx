/**
 * T132 [US6a] Integration test for aggregated balance display with hierarchical accounts
 *
 * Tests the complete integration of:
 * 1. Sidebar displaying accounts with aggregated balances
 * 2. Expand/collapse behavior for parent accounts
 * 3. Balance updates when child accounts change
 * 4. Correct indentation and visual hierarchy
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SidebarItem } from '@/components/layout/SidebarItem'
import type { SidebarCategory, SidebarAccountItem, AccountType } from '@/types/dashboard'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}))

// Track expanded accounts for tests
let mockExpandedAccounts = new Set<string>()

// Mock useExpandedAccounts hook
vi.mock('@/lib/hooks/useExpandedAccounts', () => ({
  useExpandedAccounts: () => ({
    expandedAccountIds: mockExpandedAccounts,
    isExpanded: (id: string) => mockExpandedAccounts.has(id),
    toggleExpanded: (id: string) => {
      if (mockExpandedAccounts.has(id)) {
        mockExpandedAccounts.delete(id)
      } else {
        mockExpandedAccounts.add(id)
      }
    },
    setExpanded: (id: string, expanded: boolean) => {
      if (expanded) {
        mockExpandedAccounts.add(id)
      } else {
        mockExpandedAccounts.delete(id)
      }
    },
    expandAll: (ids: string[]) => ids.forEach((id) => mockExpandedAccounts.add(id)),
    collapseAll: () => mockExpandedAccounts.clear(),
    isHydrated: true,
  }),
}))

// Build hierarchical test data
function buildTestCategory(): SidebarCategory {
  const assetAccounts: SidebarAccountItem[] = [
    {
      id: 'bank-parent',
      name: 'Bank Accounts',
      type: 'ASSET',
      balance: 100, // Parent's own balance
      parent_id: null,
      depth: 1,
      children: [
        {
          id: 'checking',
          name: 'Checking Account',
          type: 'ASSET',
          balance: 5000,
          parent_id: 'bank-parent',
          depth: 2,
          children: [
            {
              id: 'checking-usd',
              name: 'USD Checking',
              type: 'ASSET',
              balance: 2000,
              parent_id: 'checking',
              depth: 3,
              children: [],
            },
            {
              id: 'checking-twd',
              name: 'TWD Checking',
              type: 'ASSET',
              balance: 3000,
              parent_id: 'checking',
              depth: 3,
              children: [],
            },
          ],
        },
        {
          id: 'savings',
          name: 'Savings Account',
          type: 'ASSET',
          balance: 10000,
          parent_id: 'bank-parent',
          depth: 2,
          children: [],
        },
      ],
    },
    {
      id: 'cash',
      name: 'Cash on Hand',
      type: 'ASSET',
      balance: 500, // Leaf account
      parent_id: null,
      depth: 1,
      children: [],
    },
  ]

  return {
    type: 'ASSET' as AccountType,
    label: 'Assets',
    accounts: assetAccounts,
    isExpanded: false,
  }
}

describe('Sidebar Aggregation Integration', () => {
  const mockOnToggle = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset expanded accounts for each test (default collapsed)
    mockExpandedAccounts = new Set<string>()
  })

  afterEach(() => {
    mockExpandedAccounts.clear()
  })

  describe('Aggregated balance display', () => {
    it('should display aggregated balance for Bank Accounts parent', async () => {
      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Bank Accounts parent should show aggregated balance:
      // 100 (own) + 5000 (checking) + 2000 (checking-usd) + 3000 (checking-twd) + 10000 (savings) = 20100
      await waitFor(() => {
        expect(screen.getByText('Bank Accounts')).toBeInTheDocument()
      })

      // Look for the aggregated balance (20.1K)
      const bankAccountsRow = screen.getByText('Bank Accounts').closest('div')
      expect(bankAccountsRow).toHaveTextContent('20.1K')
      expect(bankAccountsRow).toHaveTextContent('(total)')
    })

    it('should display own balance for leaf accounts (no children)', async () => {
      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        expect(screen.getByText('Cash on Hand')).toBeInTheDocument()
      })

      // Cash on Hand is a leaf account with balance 500
      // Should show own balance only, no "(total)" suffix
      const cashRow = screen.getByText('Cash on Hand').closest('div')
      expect(cashRow).toHaveTextContent('500')
      expect(cashRow).not.toHaveTextContent('(total)')
    })
  })

  describe('Expand/collapse behavior', () => {
    it('should show only root-level accounts by default', async () => {
      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        // Root accounts should be visible
        expect(screen.getByText('Bank Accounts')).toBeInTheDocument()
        expect(screen.getByText('Cash on Hand')).toBeInTheDocument()
      })

      // Child accounts should be hidden by default
      expect(screen.queryByText('Checking Account')).not.toBeInTheDocument()
      expect(screen.queryByText('Savings Account')).not.toBeInTheDocument()
    })

    it('should show child accounts when parent is pre-expanded', async () => {
      // Pre-expand the bank-parent account
      mockExpandedAccounts.add('bank-parent')

      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Child accounts should be visible
      await waitFor(() => {
        expect(screen.getByText('Checking Account')).toBeInTheDocument()
        expect(screen.getByText('Savings Account')).toBeInTheDocument()
      })

      // Grandchild accounts should still be hidden
      expect(screen.queryByText('USD Checking')).not.toBeInTheDocument()
    })

    it('should show grandchild accounts when both levels are expanded', async () => {
      // Pre-expand both levels
      mockExpandedAccounts.add('bank-parent')
      mockExpandedAccounts.add('checking')

      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // All levels should be visible
      await waitFor(() => {
        expect(screen.getByText('Bank Accounts')).toBeInTheDocument()
        expect(screen.getByText('Checking Account')).toBeInTheDocument()
        expect(screen.getByText('USD Checking')).toBeInTheDocument()
        expect(screen.getByText('TWD Checking')).toBeInTheDocument()
        expect(screen.getByText('Savings Account')).toBeInTheDocument()
      })
    })
  })

  describe('Visual hierarchy', () => {
    it('should show chevron icon for parent accounts with children', async () => {
      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        // Bank Accounts has children, should have chevron button
        const chevrons = screen.getAllByTestId('chevron')
        expect(chevrons.length).toBeGreaterThan(0)
      })
    })

    it('should show expand button for collapsed parent', async () => {
      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        // Bank Accounts is collapsed by default
        const expandButton = screen.getByRole('button', { name: /expand bank/i })
        expect(expandButton).toBeInTheDocument()
      })
    })

    it('should show collapse button when parent is expanded', async () => {
      mockExpandedAccounts.add('bank-parent')

      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        const collapseButton = screen.getByRole('button', { name: /collapse bank/i })
        expect(collapseButton).toBeInTheDocument()
      })
    })
  })

  describe('Aggregated balance with intermediate levels', () => {
    it('should show correct aggregated balance for level-2 parent', async () => {
      // Pre-expand bank-parent to see Checking Account
      mockExpandedAccounts.add('bank-parent')

      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        expect(screen.getByText('Checking Account')).toBeInTheDocument()
      })

      // Checking Account aggregated balance:
      // 5000 (own) + 2000 (usd) + 3000 (twd) = 10000 = 10.0K
      const checkingRow = screen.getByText('Checking Account').closest('div')
      expect(checkingRow).toHaveTextContent('10.0K')
      expect(checkingRow).toHaveTextContent('(total)')
    })

    it('should show leaf balance without (total) suffix', async () => {
      // Expand both levels to see grandchildren
      mockExpandedAccounts.add('bank-parent')
      mockExpandedAccounts.add('checking')

      const category = buildTestCategory()

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      await waitFor(() => {
        expect(screen.getByText('USD Checking')).toBeInTheDocument()
      })

      // USD Checking is a leaf, should show 2.0K without (total)
      const usdRow = screen.getByText('USD Checking').closest('div')
      expect(usdRow).toHaveTextContent('2.0K')
      expect(usdRow).not.toHaveTextContent('(total)')
    })
  })
})
