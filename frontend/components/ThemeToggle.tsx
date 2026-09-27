import { useState } from 'react';

type Mode = 'light' | 'dark';

export default function ThemeToggle({ className = '' }: { className?: string }) {
  const [mode, setMode] = useState<Mode>(() => (document.documentElement.dataset.mode === 'dark' ? 'dark' : 'light'));

  function choose(next: Mode) {
    if (next === mode) return;
    document.documentElement.dataset.mode = next;
    try {
      localStorage.setItem('mode', next);
    } catch {}
    setMode(next);
  }

  const button = (value: Mode, label: string) => (
    <button
      type="button"
      onClick={() => choose(value)}
      aria-pressed={mode === value}
      className={`cursor-pointer border-b py-1 transition-colors duration-(--d-ui) ease-io ${
        mode === value ? 'border-accent text-ink' : 'border-transparent text-ink-dim hover:text-accent'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div role="group" aria-label="Colour mode" className={`flex items-baseline gap-1.5 text-meta ${className}`}>
      {button('light', 'Light')}
      <span aria-hidden="true" className="text-ink-faint">
        /
      </span>
      {button('dark', 'Dark')}
    </div>
  );
}
