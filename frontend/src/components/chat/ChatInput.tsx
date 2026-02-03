'use client'

import { useState, useCallback, KeyboardEvent } from 'react'
import { Send, Mic } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
  onSend: (message: string) => void
  onVoiceClick?: () => void
  disabled?: boolean
}

export function ChatInput({ onSend, onVoiceClick, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (trimmed && !disabled) {
      onSend(trimmed)
      setInput('')
    }
  }, [input, onSend, disabled])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  return (
    <div className="flex gap-2 border-t p-4">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="輸入訊息... (按 Enter 送出)"
        disabled={disabled}
        className="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        rows={2}
      />
      {onVoiceClick && (
        <Button
          onClick={onVoiceClick}
          disabled={disabled}
          size="icon"
          variant="outline"
          className="shrink-0"
          title="語音對話"
        >
          <Mic className="h-4 w-4" />
        </Button>
      )}
      <Button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        size="icon"
        className="shrink-0"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}
