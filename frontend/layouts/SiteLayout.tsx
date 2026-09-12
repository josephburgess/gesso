import { Link, usePage } from '@inertiajs/react';
import type { ReactNode } from 'react';
import Nav from '../components/Nav';

export default function SiteLayout({ children }: { children: ReactNode }) {
  const { site } = usePage().props;

  return (
    <div className="wide:flex">
      <header className="flex flex-wrap items-baseline justify-between gap-x-5 gap-y-2 border-b border-panel-hair bg-panel px-gutter py-4 wide:sticky wide:top-0 wide:h-screen wide:w-75 wide:shrink-0 wide:flex-col wide:flex-nowrap wide:items-start wide:justify-start wide:gap-block wide:border-r wide:border-b-0 wide:px-rail-x wide:pt-block">
        <Link href={site.home_href} className="border-0 text-ink">
          <span className="block font-serif text-wordmark-sm wide:text-wordmark">{site.name}</span>
          <span className="hidden text-tagline tracking-[0.04em] text-ink-meta wide:block">{site.tagline}</span>
        </Link>
        <Nav links={site.nav} />
      </header>
      <main className="min-w-0 flex-1 px-gutter pt-block pb-section">{children}</main>
    </div>
  );
}
