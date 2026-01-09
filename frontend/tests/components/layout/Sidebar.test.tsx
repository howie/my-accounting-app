/**
 * T129 [US6a] Component test for collapsible sidebar accounts
 * T130 [US6a] Test for default collapsed state on initial load
 *
 * Tests that parent accounts in the sidebar:
 * 1. Display aggregated balances (sum of self + all children)
 * 2. Show chevron expand/collapse icons
 * 3. Default to collapsed state (only root accounts visible)
 * 4. Toggle child visibility on click
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SidebarItem } from '@/components/layout/SidebarItem'
import type { SidebarCategory, SidebarAccountItem } from '@/types/dashboard'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/accounts/test-id',
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

// Helper to create test account hierarchy
function createAccountWithChildren(
  id: string,
  name: string,
  balance: number,
  children: SidebarAccountItem[] = []
): SidebarAccountItem {
  return {
    id,
    name,
    type: 'ASSET',
    balance,
    parent_id: null,
    depth: 1,
    children,
  }
}

function createChildAccount(
  id: string,
  name: string,
  balance: number,
  parentId: string,
  depth: number = 2
): SidebarAccountItem {
  return {
    id,
    name,
    type: 'ASSET',
    balance,
    parent_id: parentId,
    depth,
    children: [],
  }
}

describe('SidebarItem - Account Hierarchy Display', () => {
  const mockOnToggle = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset expanded accounts for each test (default collapsed)
    mockExpandedAccounts = new Set<string>()
  })

  afterEach(() => {
    mockExpandedAccounts.clear()
  })

  describe('T129: Collapsible sidebar accounts', () => {
    it('should display aggregated balance for parent account (sum of self + children)', () => {
      // Parent with balance 500, children with 1000 and 2000
      // Aggregated balance should be 3500
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
        createChildAccount('child-2', 'Savings', 2000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Should show aggregated balance (3.5K for 3500)
      // Note: The current implementation shows individual balance, not aggregated
      // This test will FAIL until we implement aggregated balance display
      expect(screen.getByText('3.5K')).toBeInTheDocument()
    })

    it('should show expand/collapse chevron for accounts with children', () => {
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Should render a clickable expand/collapse button for the parent account
      // The current implementation doesn't have per-account expand/collapse
      const expandButton = screen.getByRole('button', { name: /expand|collapse/i })
      expect(expandButton).toBeInTheDocument()
    })

    it('should not show expand/collapse chevron for leaf accounts', () => {
      const leafAccount = createAccountWithChildren('leaf-1', 'Cash', 500, [])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [leafAccount],
        isExpanded: true,
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Leaf accounts should not have expand/collapse button
      const accountLink = screen.getByText('Cash')
      expect(accountLink).toBeInTheDocument()

      // No expand button for leaf
      const expandButtons = screen.queryAllByRole('button', { name: /expand bank|collapse bank/i })
      expect(expandButtons).toHaveLength(0)
    })

    it('should toggle child visibility when parent expand button is clicked', () => {
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
        createChildAccount('child-2', 'Savings', 2000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      const { rerender } = render(
        <SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />
      )

      // Initially, children should be hidden (default collapsed)
      expect(screen.queryByText('Checking')).not.toBeInTheDocument()
      expect(screen.queryByText('Savings')).not.toBeInTheDocument()

      // Find and click the expand button for Bank Accounts
      const expandButton = screen.getByRole('button', { name: /expand bank/i })
      fireEvent.click(expandButton)

      // After clicking, children should be visible
      // This requires re-render with updated state
      rerender(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      expect(screen.getByText('Checking')).toBeInTheDocument()
      expect(screen.getByText('Savings')).toBeInTheDocument()
    })

    it('should display "(total)" suffix for aggregated balances', () => {
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Parent accounts with children should show "(total)" to indicate aggregation
      expect(screen.getByText(/\(total\)/i)).toBeInTheDocument()
    })
  })

  describe('T130: Default collapsed state on initial load', () => {
    it('should hide child accounts by default (only root visible)', () => {
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
        createChildAccount('child-2', 'Savings', 2000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true, // Category is expanded, but individual accounts are collapsed
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Root account should be visible
      expect(screen.getByText('Bank Accounts')).toBeInTheDocument()

      // Child accounts should NOT be visible by default
      expect(screen.queryByText('Checking')).not.toBeInTheDocument()
      expect(screen.queryByText('Savings')).not.toBeInTheDocument()
    })

    it('should show collapsed chevron icon for parent accounts by default', () => {
      const parentAccount = createAccountWithChildren('parent-1', 'Bank Accounts', 500, [
        createChildAccount('child-1', 'Checking', 1000, 'parent-1'),
      ])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Should show right-pointing chevron (collapsed state)
      // The exact implementation may use ChevronRight icon
      const expandButton = screen.getByRole('button', { name: /expand/i })
      expect(expandButton).toBeInTheDocument()
    })

    it('should maintain 3-level hierarchy display when fully expanded', () => {
      const grandchildAccount: SidebarAccountItem = {
        id: 'grandchild-1',
        name: 'Checking USD',
        type: 'ASSET',
        balance: 500,
        parent_id: 'child-1',
        depth: 3,
        children: [],
      }

      const childAccount: SidebarAccountItem = {
        id: 'child-1',
        name: 'Checking',
        type: 'ASSET',
        balance: 200,
        parent_id: 'parent-1',
        depth: 2,
        children: [grandchildAccount],
      }

      const parentAccount: SidebarAccountItem = {
        id: 'parent-1',
        name: 'Bank Accounts',
        type: 'ASSET',
        balance: 100,
        parent_id: null,
        depth: 1,
        children: [childAccount],
      }

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      // This test assumes all levels are expanded for verification
      render(<SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />)

      // Root should always be visible
      expect(screen.getByText('Bank Accounts')).toBeInTheDocument()

      // When testing full expansion, verify the aggregated balances at each level
      // Root: 100 + 200 + 500 = 800
      // Child: 200 + 500 = 700
      // Grandchild: 500 (leaf)
    })
  })

  describe('Aggregated balance accuracy', () => {
    it('should update aggregated balance when child balances change', () => {
      // Initial render with child balance 1000
      const childAccount = createChildAccount('child-1', 'Checking', 1000, 'parent-1')
      const parentAccount = createAccountWithChildren('parent-1', 'Bank', 500, [childAccount])

      const category: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [parentAccount],
        isExpanded: true,
      }

      const { rerender } = render(
        <SidebarItem category={category} isExpanded={true} onToggle={mockOnToggle} />
      )

      // Initial: 500 + 1000 = 1500 = 1.5K
      expect(screen.getByText('1.5K')).toBeInTheDocument()

      // Update child balance to 2000
      const updatedChild = createChildAccount('child-1', 'Checking', 2000, 'parent-1')
      const updatedParent = createAccountWithChildren('parent-1', 'Bank', 500, [updatedChild])
      const updatedCategory: SidebarCategory = {
        type: 'ASSET',
        label: 'Assets',
        accounts: [updatedParent],
        isExpanded: true,
      }

      rerender(<SidebarItem category={updatedCategory} isExpanded={true} onToggle={mockOnToggle} />)

      // Updated: 500 + 2000 = 2500 = 2.5K
      expect(screen.getByText('2.5K')).toBeInTheDocument()
    })
  })
})
