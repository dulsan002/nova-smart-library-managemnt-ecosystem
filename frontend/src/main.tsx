import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ApolloProvider } from '@apollo/client';
import { Toaster } from 'react-hot-toast';

import { apolloClient } from '@/lib/apollo';
import { ThemeProvider } from '@/lib/theme';
import { App } from '@/App';
import '@/index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter>
        <ThemeProvider>
          <App />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: 'nova-card !p-4 !shadow-lg',
              style: {
                background: 'var(--nova-surface)',
                color: 'var(--nova-text)',
                borderColor: 'var(--nova-border)',
              },
            }}
          />
        </ThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </React.StrictMode>,
);
