/**
 * Tests for BalanceBreakdownChart component
 *
 * Tests the donut chart visualization for balance sheet breakdowns:
 * 1. Renders chart with valid data
 * 2. Shows empty state when no data
 * 3. Handles different color variants
 * 4. Filters out zero/negative values
 * 5. Limits to top 6 categories
 * 6. Formats currency correctly
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import { BalanceBreakdownChart } from '@/components/reports/BalanceBreakdownChart'
import type { ReportEntry } from '@/types/reports'

// Mock Tremor components
vi.mock('@tremor/react', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="tremor-card" className={className}>
      {children}
    </div>
  ),
  DonutChart: ({
    data,
    category,
    index,
    valueFormatter,
  }: {
    data: Array<{ name: string; value: number }>
    category: string
    index: string
    valueFormatter?: (value: number) => string
  }) => (
    <div data-testid="tremor-donut-chart">
      {data.map((item) => (
        <div key={item.name} data-testid={`chart-item-${item.name}`}>
          <span data-testid={`chart-name-${item.name}`}>{item.name}</span>
          <span data-testid={`chart-value-${item.name}`}>
            {valueFormatter ? valueFormatter(item.value) : item.value}
          </span>
        </div>
      ))}
    </div>
  ),
  Legend: ({
    categories,
  }: {
    categories: string[]
  }) => (
    <div data-testid="tremor-legend">
      {categories.map((cat) => (
        <span key={cat} data-testid={`legend-item-${cat}`}>
          {cat}
        </span>
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
  account_id: `${name.toLowerCase()}-id`,
  name,
  amount,
  level,
  children,
})

describe('BalanceBreakdownChart', () => {
  const defaultProps = {
    title: 'Assets',
    data: [
      createMockEntry('Cash', '10000.00'),
      createMockEntry('Investments', '50000.00'),
      createMockEntry('Real Estate', '200000.00'),
    ],
    total: '260000.00',
    color: 'emerald' as const,
  }

  describe('Rendering', () => {
    it('renders card with title', () => {
      render(<BalanceBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('tremor-card')).toBeInTheDocument()
      expect(screen.getByText('Assets Breakdown')).toBeInTheDocument()
    })

    it('renders donut chart when data is available', () => {
      render(<BalanceBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('tremor-donut-chart')).toBeInTheDocument()
    })

    it('renders legend with category names', () => {
      render(<BalanceBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('tremor-legend')).toBeInTheDocument()
      expect(screen.getByTestId('legend-item-Real Estate')).toBeInTheDocument()
      expect(screen.getByTestId('legend-item-Investments')).toBeInTheDocument()
      expect(screen.getByTestId('legend-item-Cash')).toBeInTheDocument()
    })

    it('displays all chart items with correct names', () => {
      render(<BalanceBreakdownChart {...defaultProps} />)

      expect(screen.getByTestId('chart-item-Real Estate')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Investments')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cash')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows empty message when data array is empty', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[]}
          total="0"
        />
      )

      expect(screen.getByText('No data available')).toBeInTheDocument()
      expect(screen.queryByTestId('tremor-donut-chart')).not.toBeInTheDocument()
    })

    it('shows empty message when total is zero', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Cash', '0.00')]}
          total="0"
        />
      )

      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('shows empty message when all amounts are zero', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Cash', '0.00'),
            createMockEntry('Bank', '0.00'),
          ]}
          total="0"
        />
      )

      expect(screen.getByText('No data available')).toBeInTheDocument()
    })
  })

  describe('Data Processing', () => {
    it('filters out entries with zero amounts', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Cash', '1000.00'),
            createMockEntry('Empty Account', '0.00'),
            createMockEntry('Bank', '2000.00'),
          ]}
          total="3000.00"
        />
      )

      expect(screen.getByTestId('chart-item-Cash')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Bank')).toBeInTheDocument()
      expect(screen.queryByTestId('chart-item-Empty Account')).not.toBeInTheDocument()
    })

    it('handles negative amounts by using absolute value', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Negative', '-5000.00')]}
          total="5000.00"
        />
      )

      expect(screen.getByTestId('chart-item-Negative')).toBeInTheDocument()
      expect(screen.getByTestId('chart-value-Negative')).toHaveTextContent('$5,000')
    })

    it('sorts entries by amount in descending order', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[
            createMockEntry('Small', '100.00'),
            createMockEntry('Large', '10000.00'),
            createMockEntry('Medium', '1000.00'),
          ]}
          total="11100.00"
        />
      )

      const chartItems = screen.getAllByTestId(/^chart-item-/)
      expect(chartItems[0]).toHaveTextContent('Large')
      expect(chartItems[1]).toHaveTextContent('Medium')
      expect(chartItems[2]).toHaveTextContent('Small')
    })

    it('limits to top 6 categories', () => {
      const manyEntries = [
        createMockEntry('Cat1', '1000.00'),
        createMockEntry('Cat2', '2000.00'),
        createMockEntry('Cat3', '3000.00'),
        createMockEntry('Cat4', '4000.00'),
        createMockEntry('Cat5', '5000.00'),
        createMockEntry('Cat6', '6000.00'),
        createMockEntry('Cat7', '7000.00'),
        createMockEntry('Cat8', '8000.00'),
      ]

      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={manyEntries}
          total="36000.00"
        />
      )

      // Should show top 6 by amount (Cat8, Cat7, Cat6, Cat5, Cat4, Cat3)
      expect(screen.getByTestId('chart-item-Cat8')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cat7')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cat6')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cat5')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cat4')).toBeInTheDocument()
      expect(screen.getByTestId('chart-item-Cat3')).toBeInTheDocument()
      // Should NOT show Cat1 and Cat2 (lowest values)
      expect(screen.queryByTestId('chart-item-Cat1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('chart-item-Cat2')).not.toBeInTheDocument()
    })
  })

  describe('Currency Formatting', () => {
    it('formats values as USD currency', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Cash', '12345.67')]}
          total="12345.67"
        />
      )

      expect(screen.getByTestId('chart-value-Cash')).toHaveTextContent('$12,346')
    })

    it('formats large numbers with thousand separators', () => {
      render(
        <BalanceBreakdownChart
          {...defaultProps}
          data={[createMockEntry('Assets', '1234567.89')]}
          total="1234567.89"
        />
      )

      expect(screen.getByTestId('chart-value-Assets')).toHaveTextContent('$1,234,568')
    })
  })

  describe('Color Variants', () => {
    it('renders with blue color variant', () => {
      render(<BalanceBreakdownChart {...defaultProps} color="blue" />)

      expect(screen.getByTestId('tremor-donut-chart')).toBeInTheDocument()
    })

    it('renders with emerald color variant', () => {
      render(<BalanceBreakdownChart {...defaultProps} color="emerald" />)

      expect(screen.getByTestId('tremor-donut-chart')).toBeInTheDocument()
    })

    it('renders with amber color variant', () => {
      render(<BalanceBreakdownChart {...defaultProps} color="amber" />)

      expect(screen.getByTestId('tremor-donut-chart')).toBeInTheDocument()
    })

    it('renders with rose color variant', () => {
      render(<BalanceBreakdownChart {...defaultProps} color="rose" />)

      expect(screen.getByTestId('tremor-donut-chart')).toBeInTheDocument()
    })
  })

  describe('Title Variations', () => {
    it('renders with Assets title', () => {
      render(<BalanceBreakdownChart {...defaultProps} title="Assets" />)

      expect(screen.getByText('Assets Breakdown')).toBeInTheDocument()
    })

    it('renders with Liabilities title', () => {
      render(<BalanceBreakdownChart {...defaultProps} title="Liabilities" />)

      expect(screen.getByText('Liabilities Breakdown')).toBeInTheDocument()
    })

    it('renders with Equity title', () => {
      render(<BalanceBreakdownChart {...defaultProps} title="Equity" />)

      expect(screen.getByText('Equity Breakdown')).toBeInTheDocument()
    })
  })
})
