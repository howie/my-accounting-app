/**
 * Expression Parser for Amount Input
 *
 * A simple recursive descent parser for basic arithmetic expressions (+, -, *, /)
 * with proper operator precedence.
 *
 * Grammar:
 *   expr    = term (('+' | '-') term)*
 *   term    = factor (('*' | '/') factor)*
 *   factor  = NUMBER
 *
 * Example: "50+40*2" → 50 + (40*2) = 130
 *
 * Features:
 * - Safe parsing (no code execution, just tokenizing and arithmetic)
 * - Banker's rounding to 2 decimal places
 * - Operator precedence (* and / before + and -)
 * - Error handling for invalid expressions
 */

export type ParseResult =
  | { success: true; value: number; expression: string }
  | { success: false; error: string; expression: string };

type Token =
  | { type: 'number'; value: number }
  | { type: 'operator'; value: '+' | '-' | '*' | '/' }
  | { type: 'lparen' }
  | { type: 'rparen' }
  | { type: 'end' };

class Tokenizer {
  private pos = 0;
  private readonly input: string;

  constructor(input: string) {
    // Remove all whitespace
    this.input = input.replace(/\s/g, '');
  }

  peek(): Token {
    const savedPos = this.pos;
    const token = this.next();
    this.pos = savedPos;
    return token;
  }

  next(): Token {
    // Skip any remaining whitespace (shouldn't be any after constructor)
    while (this.pos < this.input.length && /\s/.test(this.input[this.pos])) {
      this.pos++;
    }

    if (this.pos >= this.input.length) {
      return { type: 'end' };
    }

    const char = this.input[this.pos];

    // Check for operators
    if (char === '+' || char === '-' || char === '*' || char === '/') {
      this.pos++;
      return { type: 'operator', value: char };
    }

    // Check for parentheses
    if (char === '(') {
      this.pos++;
      return { type: 'lparen' };
    }
    if (char === ')') {
      this.pos++;
      return { type: 'rparen' };
    }

    // Check for numbers (including decimals)
    if (/[0-9.]/.test(char)) {
      let numStr = '';
      let hasDecimal = false;

      while (this.pos < this.input.length) {
        const c = this.input[this.pos];
        if (c === '.') {
          if (hasDecimal) {
            // Multiple decimal points - invalid
            break;
          }
          hasDecimal = true;
          numStr += c;
          this.pos++;
        } else if (/[0-9]/.test(c)) {
          numStr += c;
          this.pos++;
        } else {
          break;
        }
      }

      const value = parseFloat(numStr);
      if (isNaN(value)) {
        throw new Error(`Invalid number: ${numStr}`);
      }
      return { type: 'number', value };
    }

    throw new Error(`Unexpected character: ${char}`);
  }
}

class Parser {
  private tokenizer: Tokenizer;
  private currentToken: Token;

  constructor(input: string) {
    this.tokenizer = new Tokenizer(input);
    this.currentToken = this.tokenizer.next();
  }

  private advance(): void {
    this.currentToken = this.tokenizer.next();
  }

  private expect(type: Token['type']): void {
    if (this.currentToken.type !== type) {
      throw new Error(`Expected ${type}, got ${this.currentToken.type}`);
    }
  }

  /**
   * Parse the expression and return the result
   * expr = term (('+' | '-') term)*
   */
  parse(): number {
    const result = this.parseExpression();

    if (this.currentToken.type !== 'end') {
      throw new Error('Unexpected tokens at end of expression');
    }

    return result;
  }

  private parseExpression(): number {
    let left = this.parseTerm();

    while (
      this.currentToken.type === 'operator' &&
      (this.currentToken.value === '+' || this.currentToken.value === '-')
    ) {
      const op = this.currentToken.value;
      this.advance();
      const right = this.parseTerm();

      if (op === '+') {
        left = left + right;
      } else {
        left = left - right;
      }
    }

    return left;
  }

  /**
   * term = factor (('*' | '/') factor)*
   */
  private parseTerm(): number {
    let left = this.parseFactor();

    while (
      this.currentToken.type === 'operator' &&
      (this.currentToken.value === '*' || this.currentToken.value === '/')
    ) {
      const op = this.currentToken.value;
      this.advance();
      const right = this.parseFactor();

      if (op === '*') {
        left = left * right;
      } else {
        if (right === 0) {
          throw new Error('Division by zero');
        }
        left = left / right;
      }
    }

    return left;
  }

  /**
   * factor = ('+' | '-')? (NUMBER | '(' expression ')')
   */
  private parseFactor(): number {
    // Handle unary + and -
    if (
      this.currentToken.type === 'operator' &&
      (this.currentToken.value === '+' || this.currentToken.value === '-')
    ) {
      const op = this.currentToken.value;
      this.advance();
      const value = this.parseFactor();
      return op === '-' ? -value : value;
    }

    // Handle parentheses
    if (this.currentToken.type === 'lparen') {
      this.advance(); // consume '('
      const value = this.parseExpression();
      // Re-fetch token after parsing expression (type narrowing workaround)
      const currentType = this.currentToken.type as Token['type'];
      if (currentType !== 'rparen') {
        throw new Error('Missing closing parenthesis');
      }
      this.advance(); // consume ')'
      return value;
    }

    // Handle number
    if (this.currentToken.type !== 'number') {
      throw new Error(
        `Expected number, got ${this.currentToken.type === 'operator' ? this.currentToken.value : this.currentToken.type}`
      );
    }

    const value = this.currentToken.value;
    this.advance();
    return value;
  }
}

/**
 * Apply banker's rounding (round half to even) to 2 decimal places
 */
function bankersRound(value: number): number {
  const multiplier = 100;
  const shifted = value * multiplier;
  const floor = Math.floor(shifted);
  const decimal = shifted - floor;

  // Standard rounding for non-.5 cases
  if (Math.abs(decimal - 0.5) > 0.0000001) {
    return Math.round(shifted) / multiplier;
  }

  // Banker's rounding: round to nearest even
  if (floor % 2 === 0) {
    return floor / multiplier;
  } else {
    return (floor + 1) / multiplier;
  }
}

/**
 * Check if a string is a simple number (no operators)
 */
export function isSimpleNumber(input: string): boolean {
  const trimmed = input.trim();
  if (!trimmed) return false;

  // Check if it's just a number (possibly with decimal)
  return /^[0-9]+\.?[0-9]*$/.test(trimmed) || /^[0-9]*\.[0-9]+$/.test(trimmed);
}

/**
 * Check if a string contains expression operators
 */
export function hasOperators(input: string): boolean {
  return /[+\-*/]/.test(input);
}

/**
 * Parse and evaluate a mathematical expression
 *
 * @param input - The expression string (e.g., "50+40*2")
 * @returns ParseResult with success/error and the calculated value
 */
export function parseExpression(input: string): ParseResult {
  const trimmedInput = input.trim();

  // Handle empty input
  if (!trimmedInput) {
    return {
      success: false,
      error: 'Empty expression',
      expression: input,
    };
  }

  // If it's just a simple number, return it directly
  if (isSimpleNumber(trimmedInput)) {
    const value = parseFloat(trimmedInput);
    if (isNaN(value)) {
      return {
        success: false,
        error: 'Invalid number',
        expression: input,
      };
    }
    const roundedValue = bankersRound(value);

    // Validate amount range per DI-001 (0.01 to 999,999,999.99)
    if (roundedValue < 0) {
      return {
        success: false,
        error: 'Result cannot be negative',
        expression: input,
      };
    }
    if (roundedValue > 999999999.99) {
      return {
        success: false,
        error: 'Amount must be between 0.01 and 999,999,999.99',
        expression: input,
      };
    }

    return {
      success: true,
      value: roundedValue,
      expression: input,
    };
  }

  try {
    const parser = new Parser(trimmedInput);
    const result = parser.parse();

    // Apply banker's rounding to 2 decimal places
    const roundedResult = bankersRound(result);

    // Validate amount range per DI-001 (0.01 to 999,999,999.99)
    if (roundedResult < 0) {
      return {
        success: false,
        error: 'Result cannot be negative',
        expression: input,
      };
    }

    if (roundedResult > 999999999.99) {
      return {
        success: false,
        error: 'Amount must be between 0.01 and 999,999,999.99',
        expression: input,
      };
    }

    return {
      success: true,
      value: roundedResult,
      expression: input,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Invalid expression',
      expression: input,
    };
  }
}

/**
 * Format a number for display (with thousand separators and 2 decimal places)
 */
export function formatAmount(value: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Validate that a calculated amount matches the expected value
 * Used by backend to verify expression results
 */
export function validateExpressionResult(
  expression: string,
  expectedAmount: number
): boolean {
  const result = parseExpression(expression);
  if (!result.success) return false;

  // Compare with small epsilon for floating point
  return Math.abs(result.value - expectedAmount) < 0.001;
}
