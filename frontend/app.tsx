import 'vite/modulepreload-polyfill';
import { createInertiaApp } from '@inertiajs/react';
import * as Sentry from '@sentry/react';
import type { ComponentType } from 'react';
import { createRoot } from 'react-dom/client';
import '@/app.css';
import type { Appearance } from '@/types';

const meta = (name: string) => document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content;
const sentryDsn = meta('sentry-dsn');

if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: meta('sentry-environment'),
    dataCollection: { userInfo: false, cookies: false, httpBodies: [], urlQueryParams: false },
  });
}

if (new URLSearchParams(location.search).get('preview') === '1') {
  window.addEventListener('message', (event: MessageEvent<{ type: string; value: Appearance }>) => {
    if (event.origin !== location.origin || event.data?.type !== 'appearance') return;
    const { headings, motion } = event.data.value;
    Object.assign(document.documentElement.dataset, { type: headings, motion: motion ? 'on' : 'off' });
  });
}

const pages = import.meta.glob<{ default: ComponentType }>('./pages/**/*.tsx', { eager: true });

createInertiaApp({
  resolve: (name) => pages[`./pages/${name}.tsx`],
  setup: ({ el, App, props }) => {
    createRoot(el, {
      onUncaughtError: Sentry.reactErrorHandler(),
      onCaughtError: Sentry.reactErrorHandler(),
      onRecoverableError: Sentry.reactErrorHandler(),
    }).render(<App {...props} />);
  },
  http: { xsrfCookieName: 'csrftoken', xsrfHeaderName: 'X-CSRFToken' },
});
