import type { ReactNode } from 'react';

export default function SectionLabel({ children }: { children: ReactNode }) {
  return <div className="text-label text-ink-faint uppercase">{children}</div>;
}
