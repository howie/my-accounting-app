
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import userEvent from '@testing-library/user-event'
import { TokenList } from '@/components/settings/TokenManagement/TokenList'
import { CreateTokenDialog } from '@/components/settings/TokenManagement/CreateTokenDialog'
import { RevokeTokenDialog } from '@/components/settings/TokenManagement/RevokeTokenDialog'

// Mock next-intl
vi.mock('next-intl', () => ({
    useTranslations: () => (key: string) => key,
}))

// Mock UI components
vi.mock('@/components/ui/button', () => ({
    Button: ({ children, onClick, ...props }: any) => (
        <button onClick={onClick} {...props}>
            {children}
        </button>
    ),
}))

vi.mock('@/components/ui/input', () => ({
    Input: (props: any) => <input {...props} />,
}))

vi.mock('@/components/ui/dialog', () => ({
    Dialog: ({ children, open, onOpenChange }: any) => (
        open ? <div role="dialog">{children}</div> : null
    ),
    DialogContent: ({ children }: any) => <div>{children}</div>,
    DialogHeader: ({ children }: any) => <div>{children}</div>,
    DialogTitle: ({ children }: any) => <h2>{children}</h2>,
    DialogDescription: ({ children }: any) => <p>{children}</p>,
    DialogFooter: ({ children }: any) => <footer>{children}</footer>,
}))

// Mock hooks
const mockCreateToken = vi.fn()
const mockRevokeToken = vi.fn()

vi.mock('@/lib/hooks/useTokens', () => ({
    useCreateToken: () => ({
        mutateAsync: mockCreateToken,
        isPending: false,
    }),
    useRevokeToken: () => ({
        mutateAsync: mockRevokeToken,
        isPending: false,
    }),
}))

describe('TokenManagement', () => {
    const mockTokens = [
        {
            id: '1',
            name: 'Test Token 1',
            token_prefix: 'mcp-test',
            created_at: '2024-01-01T00:00:00Z',
            last_used_at: null,
            is_active: true,
            user_id: 'user1',
        },
        {
            id: '2',
            name: 'Test Token 2',
            token_prefix: 'mcp-demo',
            created_at: '2024-01-02T00:00:00Z',
            last_used_at: '2024-01-03T00:00:00Z',
            is_active: true,
            user_id: 'user1',
        },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        Object.defineProperty(navigator, 'clipboard', {
            value: {
                writeText: vi.fn(),
            },
            writable: true,
            configurable: true,
        })
    })

    describe('TokenList', () => {
        it('renders empty state when no tokens', () => {
            render(<TokenList tokens={[]} />)
            expect(screen.getByText('noTokens')).toBeDefined()
        })

        it('renders list of tokens', () => {
            render(<TokenList tokens={mockTokens} />)
            expect(screen.getByText('Test Token 1')).toBeDefined()
            expect(screen.getByText('Test Token 2')).toBeDefined()
            expect(screen.getByText('mcp-test...')).toBeDefined()
        })

        it('copies token prefix to clipboard', async () => {
            const user = userEvent.setup()
            // Re-mock writeText in case user-event replaced it, or just ensure it's a spy we track
            // If user-event replaced it, we might need to rely on its behavior.
            // But typically we want to verify the API call.
            // Let's force our spy back if needed, OR spy on the current value.
            const writeTextSpy = vi.spyOn(navigator.clipboard, 'writeText')

            render(<TokenList tokens={mockTokens} />)

            const copyButtons = screen.getAllByTitle('copyPrefix')
            await user.click(copyButtons[0])

            expect(writeTextSpy).toHaveBeenCalledWith('mcp-test')
        })
    })

    describe('CreateTokenDialog', () => {
        it('renders dialog content when open', () => {
            render(<CreateTokenDialog isOpen={true} onClose={vi.fn()} />)
            expect(screen.getByText('createTitle')).toBeDefined()
        })

        it('validates empty name', async () => {
            const user = userEvent.setup()
            render(<CreateTokenDialog isOpen={true} onClose={vi.fn()} />)

            const submitBtn = screen.getByText('create')
            await user.click(submitBtn)

            // Since button is disabled when empty, we actually check if handle is NOT called
            // Wait, let's check the implementation again.
            // Ah, the button is disabled: disabled={createToken.isPending || !name.trim()}
            expect(submitBtn).toBeDisabled()
        })

        it('submits form with valid name', async () => {
            const user = userEvent.setup()
            mockCreateToken.mockResolvedValue({
                id: '3',
                name: 'New Token',
                token: 'mcp-new-token-secret',
                token_prefix: 'mcp-new',
                created_at: '2024-01-04T00:00:00Z',
                is_active: true,
                user_id: 'user1'
            })

            render(<CreateTokenDialog isOpen={true} onClose={vi.fn()} />)

            const input = screen.getByPlaceholderText('tokenNamePlaceholder')
            await user.type(input, 'New Token')

            const submitBtn = screen.getByText('create')
            expect(submitBtn).not.toBeDisabled()
            await user.click(submitBtn)

            expect(mockCreateToken).toHaveBeenCalledWith({ name: 'New Token' })
        })

        it('shows created token', async () => {
            const user = userEvent.setup()
            mockCreateToken.mockResolvedValue({
                id: '3',
                name: 'New Token',
                token: 'mcp-new-token-secret',
                token_prefix: 'mcp-new',
                created_at: '2024-01-04T00:00:00Z',
                is_active: true,
                user_id: 'user1'
            })

            render(<CreateTokenDialog isOpen={true} onClose={vi.fn()} />)

            const input = screen.getByPlaceholderText('tokenNamePlaceholder')
            await user.type(input, 'New Token')
            await user.click(screen.getByText('create'))

            await waitFor(() => {
                expect(screen.getByText('tokenCreated')).toBeDefined()
                expect(screen.getByText('mcp-new-token-secret')).toBeDefined()
            })
        })
    })

    describe('RevokeTokenDialog', () => {
        it('calls revoke API on confirmation', async () => {
            const user = userEvent.setup()
            const onClose = vi.fn()

            render(
                <RevokeTokenDialog
                    isOpen={true}
                    onClose={onClose}
                    token={mockTokens[0]}
                />
            )

            expect(screen.getByText('revokeTitle')).toBeDefined()
            expect(screen.getByText('revokeWarning')).toBeDefined()

            const revokeBtn = screen.getByText('revoke')
            await user.click(revokeBtn)

            expect(mockRevokeToken).toHaveBeenCalledWith('1')
            expect(onClose).toHaveBeenCalled()
        })
    })
})
