'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorPageProps {
  error: Error & { digest?: string }
  reset: () => void
}

/**
 * Global error page for unhandled errors.
 */
export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error('Global error:', error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
      <AlertTriangle className="mb-6 h-16 w-16 text-yellow-500" />
      <h1 className="mb-2 text-2xl font-bold text-foreground">Something went wrong</h1>
      <p className="mb-6 max-w-md text-center text-muted-foreground">
        An unexpected error occurred. Our team has been notified.
      </p>
      {error.message && (
        <p className="mb-6 rounded-md bg-red-50 p-3 font-mono text-sm text-red-500 dark:bg-red-950">
          {error.message}
        </p>
      )}
      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          <RefreshCw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
        <Button onClick={() => (window.location.href = '/')} variant="outline">
          <Home className="mr-2 h-4 w-4" />
          Go Home
        </Button>
      </div>
    </div>
  )
}
