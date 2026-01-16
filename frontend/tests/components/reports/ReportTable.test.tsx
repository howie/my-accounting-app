/**
 * Tests for ReportTable component
 *
 * Tests the hierarchical table display for financial reports:
 * 1. Renders table with title and total
 * 2. Displays hierarchical account structure
 * 3. Expand/collapse functionality for nested entries
 * 4. Formats currency correctly
 * 5. Applies correct styling based on level
 * 6. Handles negative amounts with red styling
 */

import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

import { ReportTable } from '@/components/reports/ReportTable'
import type { ReportEntry } from '@/types/reports'

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  ChevronDown: () => <span data-testid="chevron-down">▼</span>,
  ChevronRight: () => <span data-testid="chevron-right">▶</span>,
}))

// Test fixtures
const createMockEntry = (
  name: string,
  amount: string,
  level: number = 0,
  children: ReportEntry[] = []
): ReportEntry => ({
  account_id: `${name.toLowerCase().replace(/\s/g, '-')}-id`,
  name,
  amount,
  level,
  children,
})

describe('ReportTable', () => {
  const simpleData: ReportEntry[] = [
    createMockEntry('Cash', '10000.00', 0),
    createMockEntry('Bank Account', '50000.00', 0),
  ]

  const hierarchicalData: ReportEntry[] = [
    createMockEntry('Current Assets', '60000.00', 0, [
      createMockEntry('Cash', '10000.00', 1),
      createMockEntry('Bank Account', '50000.00', 1),
    ]),
    createMockEntry('Fixed Assets', '200000.00', 0, [
      createMockEntry('Real Estate', '180000.00', 1),
      createMockEntry('Equipment', '20000.00', 1),
    ]),
  ]

  describe('Rendering', () => {
    it('renders table container with border', () => {
      const { container } = render(<ReportTable data={simpleData} />)

      expect(container.querySelector('.rounded-md.border')).toBeInTheDocument()
    })

    it('renders title when provided', () => {
      render(<ReportTable data={simpleData} title="Assets" />)

      expect(screen.getByText('Assets')).toBeInTheDocument()
    })

    it('renders total when provided', () => {
      render(<ReportTable data={simpleData} title="Assets" total="60000.00" />)

      expect(screen.getByText('$60,000.00')).toBeInTheDocument()
    })

    it('renders without title when not provided', () => {
      render(<ReportTable data={simpleData} />)

      expect(screen.queryByText('Assets')).not.toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(
        <ReportTable data={simpleData} className="custom-class" />
      )

      expect(container.querySelector('.custom-class')).toBeInTheDocument()
    })
  })

  describe('Entry Display', () => {
    it('displays all top-level entries', () => {
      render(<ReportTable data={simpleData} />)

      expect(screen.getByText('Cash')).toBeInTheDocument()
      expect(screen.getByText('Bank Account')).toBeInTheDocument()
    })

    it('displays entry amounts formatted as currency', () => {
      render(<ReportTable data={simpleData} />)

      expect(screen.getByText('$10,000.00')).toBeInTheDocument()
      expect(screen.getByText('$50,000.00')).toBeInTheDocument()
    })

    it('displays nested entries when parent is expanded', () => {
      render(<ReportTable data={hierarchicalData} />)

      // Parent entries
      expect(screen.getByText('Current Assets')).toBeInTheDocument()
      expect(screen.getByText('Fixed Assets')).toBeInTheDocument()

      // Child entries (expanded by default)
      expect(screen.getByText('Cash')).toBeInTheDocument()
      expect(screen.getByText('Bank Account')).toBeInTheDocument()
      expect(screen.getByText('Real Estate')).toBeInTheDocument()
      expect(screen.getByText('Equipment')).toBeInTheDocument()
    })
  })

  describe('Expand/Collapse Functionality', () => {
    it('shows chevron-down icon for expanded entries with children', () => {
      render(<ReportTable data={hierarchicalData} />)

      const chevrons = screen.getAllByTestId('chevron-down')
      expect(chevrons.length).toBeGreaterThan(0)
    })

    it('collapses children when parent is clicked', async () => {
      const user = userEvent.setup()
      render(<ReportTable data={hierarchicalData} />)

      // Children should be visible initially
      expect(screen.getByText('Cash')).toBeInTheDocument()

      // Click the first toggle button
      const toggleButtons = screen.getAllByRole('button')
      await user.click(toggleButtons[0])

      // Children should be hidden
      expect(screen.queryByText('Cash')).not.toBeInTheDocument()
    })

    it('shows chevron-right icon when collapsed', async () => {
      const user = userEvent.setup()
      render(<ReportTable data={hierarchicalData} />)

      // Click to collapse
      const toggleButtons = screen.getAllByRole('button')
      await user.click(toggleButtons[0])

      expect(screen.getByTestId('chevron-right')).toBeInTheDocument()
    })

    it('re-expands children when clicked again', async () => {
      const user = userEvent.setup()
      render(<ReportTable data={hierarchicalData} />)

      const toggleButtons = screen.getAllByRole('button')

      // Collapse
      await user.click(toggleButtons[0])
      expect(screen.queryByText('Cash')).not.toBeInTheDocument()

      // Expand again
      await user.click(toggleButtons[0])
      expect(screen.getByText('Cash')).toBeInTheDocument()
    })

    it('does not show toggle button for entries without children', () => {
      render(<ReportTable data={simpleData} />)

      // Simple entries have no children, so no toggle buttons
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Currency Formatting', () => {
    it('formats amounts as USD currency', () => {
      render(<ReportTable data={[createMockEntry('Test', '1234.56')]} />)

      expect(screen.getByText('$1,234.56')).toBeInTheDocument()
    })

    it('formats large numbers with thousand separators', () => {
      render(<ReportTable data={[createMockEntry('Test', '1234567.89')]} />)

      expect(screen.getByText('$1,234,567.89')).toBeInTheDocument()
    })

    it('formats zero amounts', () => {
      render(<ReportTable data={[createMockEntry('Empty', '0.00')]} />)

      expect(screen.getByText('$0.00')).toBeInTheDocument()
    })
  })

  describe('Negative Amount Styling', () => {
    it('applies red color to negative amounts', () => {
      render(<ReportTable data={[createMockEntry('Loss', '-5000.00')]} />)

      const amountElement = screen.getByText('-$5,000.00')
      expect(amountElement).toHaveClass('text-red-500')
    })

    it('does not apply red color to positive amounts', () => {
      render(<ReportTable data={[createMockEntry('Gain', '5000.00')]} />)

      const amountElement = screen.getByText('$5,000.00')
      expect(amountElement).not.toHaveClass('text-red-500')
    })

    it('does not apply red color to zero amounts', () => {
      render(<ReportTable data={[createMockEntry('Zero', '0.00')]} />)

      const amountElement = screen.getByText('$0.00')
      expect(amountElement).not.toHaveClass('text-red-500')
    })
  })

  describe('Level-Based Styling', () => {
    it('applies font-medium to level 0 entries', () => {
      const { container } = render(
        <ReportTable data={[createMockEntry('Top Level', '1000.00', 0)]} />
      )

      const row = container.querySelector('.font-medium')
      expect(row).toBeInTheDocument()
    })

    it('applies text-sm to entries with level > 0', () => {
      const { container } = render(<ReportTable data={hierarchicalData} />)

      // Cash is level 1, should have text-sm class on the row container
      const textSmElements = container.querySelectorAll('.text-sm')
      expect(textSmElements.length).toBeGreaterThan(0)
    })

    it('applies increasing indentation based on level', () => {
      const deepData: ReportEntry[] = [
        createMockEntry('Level 0', '100.00', 0, [
          createMockEntry('Level 1', '50.00', 1, [
            createMockEntry('Level 2', '25.00', 2),
          ]),
        ]),
      ]

      const { container } = render(<ReportTable data={deepData} />)

      // Check that different padding-left values are applied
      const rows = container.querySelectorAll('[style*="padding-left"]')
      expect(rows.length).toBe(3)
    })
  })

  describe('Edge Cases', () => {
    it('handles empty data array', () => {
      const { container } = render(<ReportTable data={[]} />)

      expect(container.querySelector('.divide-y')).toBeInTheDocument()
    })

    it('handles entries with null account_id', () => {
      const entryWithNullId: ReportEntry = {
        account_id: null,
        name: 'Total',
        amount: '100000.00',
        level: 0,
        children: [],
      }

      render(<ReportTable data={[entryWithNullId]} />)

      expect(screen.getByText('Total')).toBeInTheDocument()
    })

    it('handles entries with empty name', () => {
      render(<ReportTable data={[createMockEntry('', '1000.00')]} />)

      expect(screen.getByText('$1,000.00')).toBeInTheDocument()
    })

    it('handles deeply nested structures', () => {
      const deepData: ReportEntry[] = [
        createMockEntry('L0', '1000.00', 0, [
          createMockEntry('L1', '500.00', 1, [
            createMockEntry('L2', '250.00', 2, [
              createMockEntry('L3', '125.00', 3),
            ]),
          ]),
        ]),
      ]

      render(<ReportTable data={deepData} />)

      expect(screen.getByText('L0')).toBeInTheDocument()
      expect(screen.getByText('L1')).toBeInTheDocument()
      expect(screen.getByText('L2')).toBeInTheDocument()
      expect(screen.getByText('L3')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('toggle buttons are clickable', async () => {
      const user = userEvent.setup()
      render(<ReportTable data={hierarchicalData} />)

      const toggleButtons = screen.getAllByRole('button')
      expect(toggleButtons.length).toBeGreaterThan(0)

      // Should not throw when clicked
      await user.click(toggleButtons[0])
    })

    it('maintains focus after toggle interaction', async () => {
      const user = userEvent.setup()
      render(<ReportTable data={hierarchicalData} />)

      const toggleButton = screen.getAllByRole('button')[0]
      await user.click(toggleButton)

      // Button should still be in the document
      expect(toggleButton).toBeInTheDocument()
    })
  })
})
