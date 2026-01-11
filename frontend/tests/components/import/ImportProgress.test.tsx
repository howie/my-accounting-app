/**
 * T071 [US1] Component test for ImportProgress
 *
 * Tests the progress indicator component for data import:
 * 1. Displays progress bar with correct percentage
 * 2. Shows current/total count text
 * 3. Applies correct status colors
 * 4. Updates dynamically as progress changes
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { NextIntlClientProvider } from 'next-intl'

import ImportProgress from '@/components/import/ImportProgress'
import zhTW from '../../../messages/zh-TW.json'

function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
        {children}
      </NextIntlClientProvider>
    )
  }
}

describe('ImportProgress', () => {
  describe('Rendering', () => {
    it('renders progress label', () => {
      render(
        <ImportProgress current={0} total={100} status="pending" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.progress)).toBeInTheDocument()
    })

    it('displays current and total count', () => {
      render(
        <ImportProgress current={50} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      // Check for progress text (format: "50 / 100")
      expect(screen.getByText(/50.*100/)).toBeInTheDocument()
    })

    it('displays percentage', () => {
      render(
        <ImportProgress current={25} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('25%')).toBeInTheDocument()
    })
  })

  describe('Progress Calculation', () => {
    it('calculates 0% when current is 0', () => {
      render(
        <ImportProgress current={0} total={100} status="pending" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('calculates 100% when current equals total', () => {
      render(
        <ImportProgress current={100} total={100} status="completed" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('calculates correct percentage for partial progress', () => {
      render(
        <ImportProgress current={33} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('33%')).toBeInTheDocument()
    })

    it('handles 0 total gracefully (shows 0%)', () => {
      render(
        <ImportProgress current={0} total={0} status="pending" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('rounds percentage to nearest integer', () => {
      render(
        <ImportProgress current={1} total={3} status="processing" />,
        { wrapper: createWrapper() }
      )

      // 1/3 = 33.33... should round to 33%
      expect(screen.getByText('33%')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('shows pending status text', () => {
      render(
        <ImportProgress current={0} total={100} status="pending" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.statusPending)).toBeInTheDocument()
    })

    it('shows processing status text', () => {
      render(
        <ImportProgress current={50} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.statusProcessing)).toBeInTheDocument()
    })

    it('shows completed status text', () => {
      render(
        <ImportProgress current={100} total={100} status="completed" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.statusCompleted)).toBeInTheDocument()
    })

    it('shows failed status text', () => {
      render(
        <ImportProgress current={50} total={100} status="failed" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.statusFailed)).toBeInTheDocument()
    })
  })

  describe('Progress Bar Styling', () => {
    it('applies gray color for pending status', () => {
      const { container } = render(
        <ImportProgress current={0} total={100} status="pending" />,
        { wrapper: createWrapper() }
      )

      const progressBar = container.querySelector('.bg-gray-200')
      expect(progressBar).toBeInTheDocument()
    })

    it('applies blue color for processing status', () => {
      const { container } = render(
        <ImportProgress current={50} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.bg-blue-500')
      expect(progressFill).toBeInTheDocument()
    })

    it('applies green color for completed status', () => {
      const { container } = render(
        <ImportProgress current={100} total={100} status="completed" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.bg-green-500')
      expect(progressFill).toBeInTheDocument()
    })

    it('applies red color for failed status', () => {
      const { container } = render(
        <ImportProgress current={50} total={100} status="failed" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.bg-red-500')
      expect(progressFill).toBeInTheDocument()
    })
  })

  describe('Progress Bar Width', () => {
    it('sets correct width style for progress bar', () => {
      const { container } = render(
        <ImportProgress current={50} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.bg-blue-500')
      expect(progressFill).toHaveStyle({ width: '50%' })
    })

    it('sets 0% width for no progress', () => {
      const { container } = render(
        <ImportProgress current={0} total={100} status="pending" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.h-2\\.5.rounded-full.transition-all')
      expect(progressFill).toHaveStyle({ width: '0%' })
    })

    it('sets 100% width for complete progress', () => {
      const { container } = render(
        <ImportProgress current={100} total={100} status="completed" />,
        { wrapper: createWrapper() }
      )

      const progressFill = container.querySelector('.bg-green-500')
      expect(progressFill).toHaveStyle({ width: '100%' })
    })
  })

  describe('Dynamic Updates', () => {
    it('updates percentage when props change', () => {
      const { rerender } = render(
        <ImportProgress current={25} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('25%')).toBeInTheDocument()

      rerender(
        <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
          <ImportProgress current={75} total={100} status="processing" />
        </NextIntlClientProvider>
      )

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('updates status when props change', () => {
      const { rerender } = render(
        <ImportProgress current={50} total={100} status="processing" />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(zhTW.import.statusProcessing)).toBeInTheDocument()

      rerender(
        <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
          <ImportProgress current={100} total={100} status="completed" />
        </NextIntlClientProvider>
      )

      expect(screen.getByText(zhTW.import.statusCompleted)).toBeInTheDocument()
    })
  })
})
