import type { ReactNode } from 'react';

type Props = { label: string; error?: string; className?: string; children: ReactNode };

export default function Field({ label, error, className = '', children }: Props) {
  return (
    <label className={`flex flex-col gap-1.75 ${className}`}>
      <span className="text-micro tracking-[0.08em] text-ink-dim uppercase">{label}</span>
      {children}
      {error && <span className="text-meta-sm text-accent">{error}</span>}
    </label>
  );
}
