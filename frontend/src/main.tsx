import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import '@/i18n';
import '@/globals.css';

import { ThemeProvider } from '@/lib/context/ThemeContext';
import { Providers } from '@/lib/providers';
import { router } from '@/router';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <Providers>
        <RouterProvider router={router} />
      </Providers>
    </ThemeProvider>
  </StrictMode>,
);
