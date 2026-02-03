'use client';

import { useState, useCallback, KeyboardEvent } from 'react';
import { Mic, MicOff, Send, X, Loader2 } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { useVoiceChat, VoiceStatus } from '@/hooks/useVoiceChat';

interface VoiceChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

function StatusIndicator({ status, isAiSpeaking }: { status: VoiceStatus; isAiSpeaking: boolean }) {
  if (status === 'connecting') {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>連線中...</span>
      </div>
    );
  }

  if (status === 'recording') {
    return (
      <div className="flex items-center gap-2 text-sm">
        {isAiSpeaking ? (
          <>
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-500" />
            </span>
            <span className="text-blue-600">AI 回覆中...</span>
          </>
        ) : (
          <>
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
            </span>
            <span className="text-red-600">聆聽中...</span>
          </>
        )}
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex items-center gap-2 text-sm text-destructive">
        <span className="h-3 w-3 rounded-full bg-destructive" />
        <span>連線錯誤</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="h-3 w-3 rounded-full bg-muted" />
      <span>未連線</span>
    </div>
  );
}

export function VoiceChatPanel({ isOpen, onClose }: VoiceChatPanelProps) {
  const {
    status,
    transcript,
    isAiSpeaking,
    errorMessage,
    startVoiceChat,
    stopVoiceChat,
    sendTextInterrupt,
  } = useVoiceChat();

  const [textInput, setTextInput] = useState('');

  const handleToggleVoice = useCallback(() => {
    if (status === 'recording' || status === 'connected') {
      stopVoiceChat();
    } else if (status === 'idle' || status === 'error') {
      startVoiceChat();
    }
  }, [status, startVoiceChat, stopVoiceChat]);

  const handleSendText = useCallback(() => {
    const trimmed = textInput.trim();
    if (trimmed) {
      sendTextInterrupt(trimmed);
      setTextInput('');
    }
  }, [textInput, sendTextInterrupt]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendText();
      }
    },
    [handleSendText]
  );

  const handleClose = useCallback(() => {
    if (status !== 'idle') {
      stopVoiceChat();
    }
    onClose();
  }, [status, stopVoiceChat, onClose]);

  const isActive = status === 'recording' || status === 'connected';

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <SheetContent className="flex flex-col p-0">
        <SheetHeader className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              <SheetTitle>語音對話</SheetTitle>
            </div>
            <Button variant="ghost" size="icon" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <SheetDescription>
            Gemini Live 語音助手 - 全程繁體中文對話
          </SheetDescription>
        </SheetHeader>

        {/* Status area */}
        <div className="border-b px-6 py-3">
          <StatusIndicator status={status} isAiSpeaking={isAiSpeaking} />
        </div>

        {/* Transcript area */}
        <div className="flex-1 overflow-y-auto p-6">
          {transcript ? (
            <div className="space-y-2 whitespace-pre-wrap text-sm">
              {transcript}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-center text-muted-foreground">
              <div className="space-y-2">
                <Mic className="mx-auto h-12 w-12 opacity-50" />
                <p className="text-sm">
                  點擊下方麥克風按鈕開始語音對話
                </p>
                <p className="text-xs">
                  對話過程中可以輸入文字來中斷語音
                </p>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {errorMessage}
            </div>
          )}
        </div>

        {/* Controls area */}
        <div className="space-y-3 border-t p-4">
          {/* Text interrupt input - only shown when voice is active */}
          {isActive && (
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="輸入文字中斷語音..."
                className="flex-1 rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
              <Button
                onClick={handleSendText}
                disabled={!textInput.trim()}
                size="icon"
                variant="outline"
                title="送出文字中斷"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Voice toggle button */}
          <div className="flex justify-center">
            <Button
              onClick={handleToggleVoice}
              disabled={status === 'connecting'}
              size="lg"
              variant={isActive ? 'destructive' : 'default'}
              className="h-14 w-14 rounded-full"
              title={isActive ? '停止語音' : '開始語音'}
            >
              {status === 'connecting' ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : isActive ? (
                <MicOff className="h-6 w-6" />
              ) : (
                <Mic className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
