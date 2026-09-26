import type { SocialLink } from '@/types';

export default function SocialLinks({ links, className = '' }: { links: SocialLink[]; className?: string }) {
  if (links.length === 0) return null;

  return (
    <ul className={`flex flex-wrap gap-x-4.5 gap-y-1 text-meta ${className}`}>
      {links.map((link) => (
        <li key={link.href}>
          <a href={link.href} rel="me noopener" target="_blank">
            {link.label}
          </a>
        </li>
      ))}
    </ul>
  );
}
