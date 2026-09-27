import { Link, usePage } from '@inertiajs/react';
import SocialLinks from '@/components/SocialLinks';

type Props = { className?: string; socialClassName?: string };

export default function SiteFooter({ className = '', socialClassName = '' }: Props) {
  const { site } = usePage().props;
  if (site.social.length === 0 && site.pages.length === 0) return null;

  return (
    <footer
      className={`flex flex-wrap items-baseline justify-between gap-x-6 gap-y-3 border-t border-hair pt-slot ${className}`}
    >
      <SocialLinks links={site.social} className={socialClassName} />
      {site.pages.length > 0 && (
        <ul className="flex flex-wrap gap-x-4.5 gap-y-1 text-meta-sm">
          {site.pages.map((page) => (
            <li key={page.href}>
              <Link href={page.href} className="border-0 text-ink-dim hover:text-accent">
                {page.label}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </footer>
  );
}
