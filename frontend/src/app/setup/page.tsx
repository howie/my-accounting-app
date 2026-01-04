'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSetupUser } from '@/lib/hooks/useUser'

export default function SetupPage() {
  const router = useRouter()
  const setupUser = useSetupUser()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim()) {
      setError('Email is required')
      return
    }

    try {
      await setupUser.mutateAsync({ email: email.trim() })
      router.push('/ledgers')
    } catch {
      setError('Failed to create user. Please try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Welcome to LedgerOne</h1>
          <p className="mt-2 text-muted-foreground">
            Set up your account to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email Address
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1"
              disabled={setupUser.isPending}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={setupUser.isPending}
          >
            {setupUser.isPending ? 'Setting up...' : 'Get Started'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          This is a single-user application. Your data is stored locally.
        </p>
      </div>
    </div>
  )
}
