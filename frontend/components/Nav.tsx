import { Link } from '@inertiajs/react';
import type { NavLink } from '@/types';

export default function Nav({ links, inline }: { links: NavLink[]; inline?: boolean }) {
  return (
    <nav className={`flex gap-4.5 ${inline ? '' : 'wide:flex-col wide:items-start wide:gap-1'}`}>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={link.current ? 'page' : undefined}
          className="border-b border-transparent py-1 text-nav text-ink hover:text-accent aria-[current=page]:border-accent"
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
