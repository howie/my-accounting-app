import { Outlet } from 'react-router-dom';
import { SettingsNav } from '@/components/settings/SettingsNav';

/**
 * Settings section layout with sidebar navigation.
 * Replaces Next.js app/settings/layout.tsx.
 */
export function SettingsLayout() {
  return (
    <div className="flex gap-8 p-6">
      <SettingsNav />
      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
