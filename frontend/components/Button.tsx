import type { ComponentProps } from 'react';

export default function Button({ className = '', ...props }: ComponentProps<'button'>) {
  return (
    <button
      {...props}
      className={`bg-ink tracking-[0.03em] text-paper transition-colors duration-(--d-state) hover:bg-accent disabled:opacity-60 ${className}`}
    />
  );
}
