

import { cn } from '@/lib/utils'
import type { ChatMessage as ChatMessageType } from '@/lib/context/ChatContext'
import { Bot, User } from 'lucide-react'

interface ChatMessageProps {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn('flex gap-3 p-4', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          'flex max-w-[80%] flex-col gap-1 rounded-lg px-3 py-2',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.toolCalls.map((tc, idx) => (
              <div
                key={idx}
                className="text-xs rounded bg-background/50 px-2 py-1"
              >
                <span className="font-medium">{tc.tool_name}</span>
                {tc.result.success !== undefined && (
                  <span className={tc.result.success ? 'text-green-600' : 'text-red-600'}>
                    {' '}
                    ({tc.result.success ? '成功' : '失敗'})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
