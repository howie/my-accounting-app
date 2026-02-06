import { Outlet } from 'react-router-dom';
import { AppShell } from './AppShell';
import { Footer } from '@/components/ui/Footer';

/**
 * Root route layout for React Router.
 * Replaces Next.js app/layout.tsx.
 */
export function RootLayout() {
  return (
    <>
      <AppShell>
        <Outlet />
      </AppShell>
      <Footer />
    </>
  );
}
