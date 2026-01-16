/**
 * Tests for IncomeExpenseBreakdownChart component
 *
 * Tests the bar list visualization for income/expense breakdowns:
 * 1. Renders chart with valid data
 * 2. Shows empty state when no data
 * 3. Displays total amount in header
 * 4. Shows percentage breakdown
 * 5. Filters out zero/negative values
 * 6. Limits to top 8 categories
 * 7. Handles different color variants (amber/rose)
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import { IncomeExpenseBreakdownChart } from '@/components/reports/IncomeExpenseBreakdownChart'
import type { ReportEntry } from '@/types/reports'

// Mock Tremor components
vi.mock('@tremor/react', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="tremor-card" className={className}>
      {children}
    </div>
  ),
  BarList: ({
    data,
    valueFormatter,
    color,
  }: {
    data: Array<{ name: string; value: number }>
    valueFormatter?: (value: number) => string
    color?: string
  }) => (
    <div data-testid="tremor-bar-list" data-color={color}>
      {data.map((item) => (
        <div key={item.name} data-testid={`bar-item-${item.name}`}>
          <span data-testid={`bar-name-${item.name}`}>{item.name}</span>
          <span data-testid={`bar-value-${item.name}`}>
            {valueFormatter ? valueFormatter(item.value) : item.value}
          </span>
        </div>
      ))}
    </div>
  ),
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

describe('IncomeExpenseBreakdownChart', () => {
  const defaultProps = {
    title: 'Income',
    data: [
      createMockEntry('Salary', '5000.00'),
      createMockEntry('Freelance', '2000.00'),
      createMockEntry('Dividends', '500.00'),
    ],
    total: '7500.00',
    color: 'amber' as const,
  }

  describe('Rendering', () => {
    it('renders card with title', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('tremor-card')).toBeInTheDocument()
      expect(screen.getByText('Income Breakdown')).toBeInTheDocument()
    })

    it('displays total amount in header', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} />)

      expect(screen.getByText('$7,500')).toBeInTheDocument()
    })

    it('renders bar list when data is available', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('tremor-bar-list')).toBeInTheDocument()
    })

    it('displays all bar items with correct names', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('bar-item-Salary')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Freelance')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Dividends')).toBeInTheDocument()
    })

    it('passes correct color to BarList', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} color="amber" />)

      expect(screen.getByTestId('tremor-bar-list')).toHaveAttribute('data-color', 'amber')
    })
  })

  describe('Empty State', () => {
    it('shows empty message when data array is empty', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[]}
          total="0"
        />
      )

      expect(screen.getByText('No data for this period')).toBeInTheDocument()
      expect(screen.queryByTestId('tremor-bar-list')).not.toBeInTheDocument()
    })

    it('shows empty message when total is zero', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Income', '0.00')]}
          total="0"
        />
      )

      expect(screen.getByText('No data for this period')).toBeInTheDocument()
    })

    it('shows empty message when all amounts are zero', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Salary', '0.00'),
            createMockEntry('Bonus', '0.00'),
          ]}
          total="0"
        />
      )

      expect(screen.getByText('No data for this period')).toBeInTheDocument()
    })
  })

  describe('Data Processing', () => {
    it('filters out entries with zero amounts', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Salary', '5000.00'),
            createMockEntry('Empty', '0.00'),
            createMockEntry('Bonus', '1000.00'),
          ]}
          total="6000.00"
        />
      )

      expect(screen.getByTestId('bar-item-Salary')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Bonus')).toBeInTheDocument()
      expect(screen.queryByTestId('bar-item-Empty')).not.toBeInTheDocument()
    })

    it('handles negative amounts by using absolute value', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Expense', '-1000.00')]}
          total="-1000.00"
        />
      )

      expect(screen.getByTestId('bar-item-Expense')).toBeInTheDocument()
      // Total in header should be positive
      expect(screen.getByText('$1,000')).toBeInTheDocument()
    })

    it('sorts entries by amount in descending order', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Small', '100.00'),
            createMockEntry('Large', '10000.00'),
            createMockEntry('Medium', '1000.00'),
          ]}
          total="11100.00"
        />
      )

      const barItems = screen.getAllByTestId(/^bar-item-/)
      expect(barItems[0]).toHaveTextContent('Large')
      expect(barItems[1]).toHaveTextContent('Medium')
      expect(barItems[2]).toHaveTextContent('Small')
    })

    it('limits to top 8 categories', () => {
      const manyEntries = Array.from({ length: 10 }, (_, i) =>
        createMockEntry(`Category${i + 1}`, `${(i + 1) * 1000}.00`)
      )

      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={manyEntries}
          total="55000.00"
        />
      )

      // Should show top 8 by amount (Category10 down to Category3)
      expect(screen.getByTestId('bar-item-Category10')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category9')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category8')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category7')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category6')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category5')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category4')).toBeInTheDocument()
      expect(screen.getByTestId('bar-item-Category3')).toBeInTheDocument()
      // Should NOT show Category1 and Category2 (lowest values)
      expect(screen.queryByTestId('bar-item-Category1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('bar-item-Category2')).not.toBeInTheDocument()
    })
  })

  describe('Currency and Percentage Formatting', () => {
    it('formats values as USD currency with percentage', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Salary', '5000.00')]}
          total="5000.00"
        />
      )

      // Should show "$5,000 (100.0%)"
      expect(screen.getByTestId('bar-value-Salary')).toHaveTextContent('$5,000')
      expect(screen.getByTestId('bar-value-Salary')).toHaveTextContent('100.0%')
    })

    it('calculates correct percentages for multiple items', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Half', '500.00'),
            createMockEntry('Quarter', '250.00'),
          ]}
          total="1000.00"
        />
      )

      expect(screen.getByTestId('bar-value-Half')).toHaveTextContent('50.0%')
      expect(screen.getByTestId('bar-value-Quarter')).toHaveTextContent('25.0%')
    })

    it('formats large numbers with thousand separators', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Big Income', '1234567.89')]}
          total="1234567.89"
        />
      )

      expect(screen.getByTestId('bar-value-Big Income')).toHaveTextContent('$1,234,568')
    })
  })

  describe('Color Variants', () => {
    it('renders with amber color for income', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} color="amber" />)

      expect(screen.getByTestId('tremor-bar-list')).toHaveAttribute('data-color', 'amber')
    })

    it('renders with rose color for expenses', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          title="Expenses"
          color="rose"
        />
      )

      expect(screen.getByTestId('tremor-bar-list')).toHaveAttribute('data-color', 'rose')
    })
  })

  describe('Title Variations', () => {
    it('renders with Income title', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} title="Income" />)

      expect(screen.getByText('Income Breakdown')).toBeInTheDocument()
    })

    it('renders with Expenses title', () => {
      render(<IncomeExpenseBreakdownChart {...defaultProps} title="Expenses" />)

      expect(screen.getByText('Expenses Breakdown')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles entries with very small amounts', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Tiny', '0.01')]}
          total="0.01"
        />
      )

      expect(screen.getByTestId('bar-item-Tiny')).toBeInTheDocument()
    })

    it('handles entries with decimal amounts', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Precise', '1234.56')]}
          total="1234.56"
        />
      )

      expect(screen.getByTestId('bar-value-Precise')).toHaveTextContent('$1,235')
    })

    it('handles negative total correctly', () => {
      render(
        <IncomeExpenseBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Expense', '-500.00')]}
          total="-500.00"
        />
      )

      // Should show absolute value in header
      expect(screen.getByText('$500')).toBeInTheDocument()
    })
  })
})
