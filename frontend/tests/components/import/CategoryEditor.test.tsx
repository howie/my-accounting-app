/**
 * T071 [US3] Component test for CategoryEditor
 *
 * Tests the category editor component for credit card import:
 * 1. Displays category value
 * 2. Shows confidence indicator with correct color
 * 3. Shows matched keyword tooltip
 * 4. Handles different confidence levels (high/medium/low)
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

import CategoryEditor from '@/components/import/CategoryEditor'

describe('CategoryEditor', () => {
  describe('Rendering', () => {
    it('displays the category value', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.85,
            matched_keyword: '餐廳',
          }}
          value="E-餐飲費"
        />
      )

      expect(screen.getByText('E-餐飲費')).toBeInTheDocument()
    })

    it('renders without suggestion', () => {
      render(<CategoryEditor suggestion={null} value="E-其他支出" />)

      expect(screen.getByText('E-其他支出')).toBeInTheDocument()
    })
  })

  describe('Confidence Indicator', () => {
    it('shows high confidence label for >= 0.8', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.9,
            matched_keyword: '餐廳',
          }}
          value="E-餐飲費"
        />
      )

      expect(screen.getByText('高')).toBeInTheDocument()
    })

    it('shows medium confidence label for >= 0.5 and < 0.8', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-交通費',
            confidence: 0.6,
            matched_keyword: '加油',
          }}
          value="E-交通費"
        />
      )

      expect(screen.getByText('中')).toBeInTheDocument()
    })

    it('shows low confidence label for < 0.5', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-其他支出',
            confidence: 0.3,
            matched_keyword: null,
          }}
          value="E-其他支出"
        />
      )

      expect(screen.getByText('低')).toBeInTheDocument()
    })

    it('does not show confidence label when no suggestion', () => {
      render(<CategoryEditor suggestion={null} value="E-餐飲費" />)

      expect(screen.queryByText('高')).not.toBeInTheDocument()
      expect(screen.queryByText('中')).not.toBeInTheDocument()
      expect(screen.queryByText('低')).not.toBeInTheDocument()
    })
  })

  describe('Confidence Colors', () => {
    it('applies green styling for high confidence', () => {
      const { container } = render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.85,
            matched_keyword: '餐廳',
          }}
          value="E-餐飲費"
        />
      )

      const badge = container.querySelector('.text-green-600')
      expect(badge).toBeInTheDocument()
    })

    it('applies yellow styling for medium confidence', () => {
      const { container } = render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-交通費',
            confidence: 0.6,
            matched_keyword: '加油',
          }}
          value="E-交通費"
        />
      )

      const badge = container.querySelector('.text-yellow-600')
      expect(badge).toBeInTheDocument()
    })

    it('applies gray styling for low confidence', () => {
      const { container } = render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-其他支出',
            confidence: 0.3,
            matched_keyword: null,
          }}
          value="E-其他支出"
        />
      )

      const badge = container.querySelector('.text-gray-500')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Tooltip', () => {
    it('shows matched keyword in tooltip when available', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.85,
            matched_keyword: '星巴克',
          }}
          value="E-餐飲費"
        />
      )

      const categoryElement = screen.getByText('E-餐飲費')
      expect(categoryElement).toHaveAttribute('title', '匹配關鍵字: 星巴克')
    })

    it('shows confidence percentage in tooltip on confidence label', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.85,
            matched_keyword: '餐廳',
          }}
          value="E-餐飲費"
        />
      )

      const confidenceLabel = screen.getByText('高')
      expect(confidenceLabel).toHaveAttribute('title', '信心度: 85%')
    })

    it('does not show matched keyword tooltip when null', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-其他支出',
            confidence: 0.3,
            matched_keyword: null,
          }}
          value="E-其他支出"
        />
      )

      const categoryElement = screen.getByText('E-其他支出')
      expect(categoryElement).not.toHaveAttribute('title')
    })
  })

  describe('Edge Cases', () => {
    it('handles 0 confidence', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: null,
            suggested_account_name: 'E-其他支出',
            confidence: 0,
            matched_keyword: null,
          }}
          value="E-其他支出"
        />
      )

      expect(screen.getByText('低')).toBeInTheDocument()
    })

    it('handles exactly 0.5 confidence as medium', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-日用品',
            confidence: 0.5,
            matched_keyword: '全聯',
          }}
          value="E-日用品"
        />
      )

      expect(screen.getByText('中')).toBeInTheDocument()
    })

    it('handles exactly 0.8 confidence as high', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-餐飲費',
            confidence: 0.8,
            matched_keyword: '便當',
          }}
          value="E-餐飲費"
        />
      )

      expect(screen.getByText('高')).toBeInTheDocument()
    })

    it('handles 1.0 confidence', () => {
      render(
        <CategoryEditor
          suggestion={{
            suggested_account_id: 'acc-1',
            suggested_account_name: 'E-娛樂費',
            confidence: 1.0,
            matched_keyword: 'Netflix',
          }}
          value="E-娛樂費"
        />
      )

      expect(screen.getByText('高')).toBeInTheDocument()
      expect(screen.getByTitle('信心度: 100%')).toBeInTheDocument()
    })
  })
})
