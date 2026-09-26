import { useState } from 'react';

export default function ThemeToggle({ className = '' }: { className?: string }) {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'charcoal');

  function toggle() {
    const theme = dark ? 'paper' : 'charcoal';
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem('theme', theme);
    } catch {}
    setDark(!dark);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`cursor-pointer py-1 text-meta text-ink-meta transition-colors duration-(--d-ui) ease-io hover:text-accent ${className}`}
    >
      {dark ? 'Light' : 'Dark'}
    </button>
  );
}
