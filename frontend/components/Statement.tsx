import type { ReactNode } from 'react';

export default function Statement({ className = '', children }: { className?: string; children: ReactNode }) {
  return <p className={`mb-0 font-serif text-display leading-[1.8] text-ink ${className}`}>{children}</p>;
}
