import { useCallback, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageCircle, Trash2 } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { useChatContext } from '@/lib/context/ChatContext'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { chatApi } from '@/lib/api/chat'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'

export function ChatPanel() {
  const { t } = useTranslation()
  const { isOpen, closeChat, messages, addMessage, clearMessages, isLoading, setIsLoading } =
    useChatContext()
  const { currentLedger } = useLedgerContext()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(
    async (content: string) => {
      // Add user message
      const userMessage = {
        id: crypto.randomUUID(),
        role: 'user' as const,
        content,
        createdAt: new Date(),
      }
      addMessage(userMessage)
      setIsLoading(true)

      try {
        const response = await chatApi.sendMessage({
          message: content,
          ledger_id: currentLedger?.id,
        })

        // Add assistant message
        const assistantMessage = {
          id: response.id,
          role: 'assistant' as const,
          content: response.message,
          toolCalls: response.tool_calls,
          createdAt: new Date(response.created_at),
        }
        addMessage(assistantMessage)
      } catch (error) {
        // Add error message
        const errorMessage = {
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: `發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`,
          createdAt: new Date(),
        }
        addMessage(errorMessage)
      } finally {
        setIsLoading(false)
      }
    },
    [addMessage, currentLedger?.id, setIsLoading]
  )

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && closeChat()}>
      <SheetContent className="flex flex-col p-0">
        <SheetHeader className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              <SheetTitle>{t('chat.title')}</SheetTitle>
            </div>
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="icon"
                onClick={clearMessages}
                title={t('chat.clearHistory')}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
          <SheetDescription>
            {currentLedger
              ? t('chat.currentLedger', { name: currentLedger.name })
              : t('chat.selectLedgerFirst')}
          </SheetDescription>
        </SheetHeader>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center p-6 text-center text-muted-foreground">
              <div className="space-y-2">
                <MessageCircle className="mx-auto h-12 w-12 opacity-50" />
                <p className="text-sm">{t('chat.welcomeMessage')}</p>
                <p className="text-xs">{t('chat.tryExample')}</p>
              </div>
            </div>
          ) : (
            <div className="divide-y">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex gap-3 p-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <MessageCircle className="h-4 w-4 animate-pulse" />
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-muted-foreground">{t('chat.thinking')}</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <ChatInput onSend={handleSend} disabled={isLoading || !currentLedger} />
      </SheetContent>
    </Sheet>
  )
}
