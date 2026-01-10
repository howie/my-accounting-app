/**
 * T016 [US1] Unit test for expression parser
 *
 * Tests the expression parser utility that evaluates arithmetic expressions
 * entered in the amount field with proper operator precedence and banker's rounding.
 */
import { describe, it, expect } from 'vitest'
import {
  parseExpression,
  isSimpleNumber,
  hasOperators,
  formatAmount,
  validateExpressionResult,
} from '@/lib/utils/expressionParser'

describe('expressionParser', () => {
  describe('parseExpression', () => {
    describe('simple numbers', () => {
      it('should parse a simple integer', () => {
        const result = parseExpression('100')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })

      it('should parse a simple decimal', () => {
        const result = parseExpression('100.50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100.5)
        }
      })

      it('should handle leading decimal point', () => {
        const result = parseExpression('.50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(0.5)
        }
      })

      it('should handle trailing decimal point', () => {
        const result = parseExpression('100.')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })
    })

    describe('basic arithmetic', () => {
      it('should parse addition: 50+50', () => {
        const result = parseExpression('50+50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })

      it('should parse subtraction: 100-30', () => {
        const result = parseExpression('100-30')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(70)
        }
      })

      it('should parse multiplication: 10*5', () => {
        const result = parseExpression('10*5')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(50)
        }
      })

      it('should parse division: 100/4', () => {
        const result = parseExpression('100/4')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(25)
        }
      })
    })

    describe('operator precedence', () => {
      it('should respect multiplication over addition: 50+40*2', () => {
        // Should be 50 + (40*2) = 50 + 80 = 130, not (50+40)*2 = 180
        const result = parseExpression('50+40*2')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(130)
        }
      })

      it('should respect division over subtraction: 100-80/2', () => {
        // Should be 100 - (80/2) = 100 - 40 = 60, not (100-80)/2 = 10
        const result = parseExpression('100-80/2')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(60)
        }
      })

      it('should handle chained operations: 10+20*3-5', () => {
        // 10 + (20*3) - 5 = 10 + 60 - 5 = 65
        const result = parseExpression('10+20*3-5')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(65)
        }
      })
    })

    describe('parentheses', () => {
      it('should handle parentheses: (50+40)*2', () => {
        const result = parseExpression('(50+40)*2')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(180)
        }
      })

      it('should handle nested parentheses: ((10+5)*2)+10', () => {
        const result = parseExpression('((10+5)*2)+10')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(40)
        }
      })

      it('should handle division in parentheses: 100/(2+2)', () => {
        const result = parseExpression('100/(2+2)')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(25)
        }
      })
    })

    describe('unary operators', () => {
      it('should handle unary minus: -50+100', () => {
        const result = parseExpression('-50+100')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(50)
        }
      })

      it('should handle unary plus: +50+50', () => {
        const result = parseExpression('+50+50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })

      it('should handle negative in parentheses: 100+(-20)', () => {
        const result = parseExpression('100+(-20)')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(80)
        }
      })
    })

    describe('whitespace handling', () => {
      it('should ignore whitespace: 50 + 50', () => {
        const result = parseExpression('50 + 50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })

      it('should handle leading/trailing whitespace: "  100  "', () => {
        const result = parseExpression('  100  ')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })
    })

    describe("banker's rounding (round half to even)", () => {
      it('should round 2.345 to 2.34 (round down to even)', () => {
        const result = parseExpression('2.345')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(2.34)
        }
      })

      it('should round 2.355 to 2.36 (round up to even)', () => {
        const result = parseExpression('2.355')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(2.36)
        }
      })

      it('should round 2.365 to 2.36 (round down to even)', () => {
        const result = parseExpression('2.365')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(2.36)
        }
      })

      it('should round expression result: 100/3', () => {
        // 100/3 = 33.333... -> 33.33
        const result = parseExpression('100/3')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(33.33)
        }
      })
    })

    describe('amount validation', () => {
      it('should reject negative result', () => {
        const result = parseExpression('50-100')
        expect(result.success).toBe(false)
        if (!result.success) {
          expect(result.error).toContain('negative')
        }
      })

      it('should reject amount exceeding max (999,999,999.99)', () => {
        // 1,000,000,001 exceeds max
        const result = parseExpression('1000000001')
        expect(result.success).toBe(false)
        if (!result.success) {
          expect(result.error).toContain('999,999,999.99')
        }
      })

      it('should accept maximum valid amount: 999999999.99', () => {
        const result = parseExpression('999999999.99')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(999999999.99)
        }
      })
    })

    describe('error cases', () => {
      it('should fail on empty input', () => {
        const result = parseExpression('')
        expect(result.success).toBe(false)
      })

      it('should fail on whitespace-only input', () => {
        const result = parseExpression('   ')
        expect(result.success).toBe(false)
      })

      it('should fail on division by zero', () => {
        const result = parseExpression('100/0')
        expect(result.success).toBe(false)
        if (!result.success) {
          expect(result.error.toLowerCase()).toContain('zero')
        }
      })

      it('should fail on invalid characters', () => {
        const result = parseExpression('100$50')
        expect(result.success).toBe(false)
      })

      it('should fail on unclosed parenthesis', () => {
        const result = parseExpression('(50+50')
        expect(result.success).toBe(false)
      })

      it('should handle consecutive operators as unary: 50++50 = 100', () => {
        // Parser interprets '++' as binary plus followed by unary plus
        // 50 + (+50) = 100
        const result = parseExpression('50++50')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(100)
        }
      })

      it('should fail on trailing operator', () => {
        const result = parseExpression('50+')
        expect(result.success).toBe(false)
      })
    })

    describe('real-world scenarios', () => {
      it('should calculate split bill: 1500/4', () => {
        const result = parseExpression('1500/4')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(375)
        }
      })

      it('should calculate with tip: 500+500*0.15', () => {
        // 500 + (500*0.15) = 500 + 75 = 575
        const result = parseExpression('500+500*0.15')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(575)
        }
      })

      it('should calculate subtotal: 100+200+300', () => {
        const result = parseExpression('100+200+300')
        expect(result.success).toBe(true)
        if (result.success) {
          expect(result.value).toBe(600)
        }
      })
    })
  })

  describe('isSimpleNumber', () => {
    it('should return true for integers', () => {
      expect(isSimpleNumber('100')).toBe(true)
    })

    it('should return true for decimals', () => {
      expect(isSimpleNumber('100.50')).toBe(true)
    })

    it('should return false for expressions', () => {
      expect(isSimpleNumber('50+50')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(isSimpleNumber('')).toBe(false)
    })
  })

  describe('hasOperators', () => {
    it('should return true for addition', () => {
      expect(hasOperators('50+50')).toBe(true)
    })

    it('should return true for subtraction', () => {
      expect(hasOperators('100-50')).toBe(true)
    })

    it('should return true for multiplication', () => {
      expect(hasOperators('10*5')).toBe(true)
    })

    it('should return true for division', () => {
      expect(hasOperators('100/4')).toBe(true)
    })

    it('should return false for simple number', () => {
      expect(hasOperators('100')).toBe(false)
    })
  })

  describe('formatAmount', () => {
    it('should format with thousand separators', () => {
      expect(formatAmount(1000)).toBe('1,000.00')
    })

    it('should format with two decimal places', () => {
      expect(formatAmount(100)).toBe('100.00')
    })

    it('should format large numbers correctly', () => {
      expect(formatAmount(999999999.99)).toBe('999,999,999.99')
    })
  })

  describe('validateExpressionResult', () => {
    it('should return true when expression matches expected amount', () => {
      expect(validateExpressionResult('50+50', 100)).toBe(true)
    })

    it('should return false when expression does not match', () => {
      expect(validateExpressionResult('50+50', 99)).toBe(false)
    })

    it('should return false for invalid expression', () => {
      expect(validateExpressionResult('invalid', 100)).toBe(false)
    })

    it('should handle floating point precision', () => {
      expect(validateExpressionResult('100/3', 33.33)).toBe(true)
    })
  })
})
