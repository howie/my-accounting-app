

import { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { Input } from '@/components/ui/input'
import {
  parseExpression,
  hasOperators,
  formatAmount,
} from '@/lib/utils/expressionParser'

interface AmountInputProps {
  /** Current input value (expression or number string) */
  value: string
  /** Callback when input changes */
  onChange: (value: string) => void
  /** Callback when a valid amount is calculated */
  onAmountCalculated: (amount: number, expression: string | null) => void
  /** HTML id attribute */
  id?: string
  /** Placeholder text */
  placeholder?: string
  /** Whether the field is required */
  required?: boolean
  /** Whether the input is disabled */
  disabled?: boolean
  /** External error message */
  error?: string | null
  /** Test ID for testing */
  'data-testid'?: string
}

/**
 * AmountInput - A smart input field for monetary amounts
 *
 * Features:
 * - Accepts simple numbers or arithmetic expressions (e.g., "50+40*2")
 * - Auto-calculates expressions on blur
 * - Displays calculated result with proper formatting
 * - Preserves original expression for audit trail
 * - Supports banker's rounding (round half to even)
 * - Shows validation errors for invalid expressions
 */
export function AmountInput({
  value,
  onChange,
  onAmountCalculated,
  id,
  placeholder = '0.00',
  required,
  disabled,
  error: externalError,
  'data-testid': testId,
}: AmountInputProps) {
  const { t } = useTranslation()
  const [calculatedAmount, setCalculatedAmount] = useState<number | null>(null)
  const [internalError, setInternalError] = useState<string | null>(null)
  const [showCalculated, setShowCalculated] = useState(false)

  // Reset calculated state when value changes
  useEffect(() => {
    if (value === '' || value === '0') {
      setCalculatedAmount(null)
      setShowCalculated(false)
      setInternalError(null)
    }
  }, [value])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value
      onChange(newValue)
      setShowCalculated(false)
      setInternalError(null)
    },
    [onChange]
  )

  const handleBlur = useCallback(() => {
    if (!value.trim()) {
      setCalculatedAmount(null)
      setInternalError(null)
      return
    }

    const result = parseExpression(value)

    if (result.success) {
      setCalculatedAmount(result.value)
      setInternalError(null)
      setShowCalculated(hasOperators(value))

      // Notify parent with calculated amount and expression (if any)
      onAmountCalculated(
        result.value,
        hasOperators(value) ? value : null
      )
    } else {
      setCalculatedAmount(null)
      setInternalError(result.error)
    }
  }, [value, onAmountCalculated])

  const handleFocus = useCallback(() => {
    setShowCalculated(false)
  }, [])

  // Determine which error to show
  const displayError = externalError || internalError

  return (
    <div className="space-y-1">
      <div className="relative">
        <Input
          id={id}
          type="text"
          inputMode="decimal"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          data-testid={testId}
          className={displayError ? 'border-destructive' : ''}
          aria-invalid={!!displayError}
          aria-describedby={displayError ? `${id}-error` : undefined}
        />
        {/* Show calculated result badge when expression was evaluated */}
        {showCalculated && calculatedAmount !== null && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <span
              className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
              data-testid={testId ? `${testId}-result` : undefined}
            >
              = {formatAmount(calculatedAmount)}
            </span>
          </div>
        )}
      </div>

      {/* Error message */}
      {displayError && (
        <p
          id={`${id}-error`}
          className="text-xs text-destructive"
          role="alert"
          data-testid={testId ? `${testId}-error` : undefined}
        >
          {displayError}
        </p>
      )}

      {/* Expression hint */}
      {!displayError && hasOperators(value) && !showCalculated && (
        <p className="text-xs text-muted-foreground">
          {t('transactionEntry.expressionHint')}
        </p>
      )}
    </div>
  )
}
