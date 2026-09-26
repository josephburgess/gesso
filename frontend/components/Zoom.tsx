import type { ReactNode } from 'react';

export default function Zoom({ className = '', children }: { className?: string; children: ReactNode }) {
  return (
    <div className={`group/zoom overflow-hidden bg-image-bg ${className}`}>
      <div className="transition-transform duration-(--d-image) ease-out group-hover/zoom:scale-102">{children}</div>
    </div>
  );
}
