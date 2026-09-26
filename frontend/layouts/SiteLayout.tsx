import { Head, Link, usePage } from '@inertiajs/react';
import type { ReactNode } from 'react';
import Nav from '@/components/Nav';
import ThemeToggle from '@/components/ThemeToggle';

type Props = { title?: string; rail?: ReactNode; children: ReactNode };

export default function SiteLayout({ title, rail, children }: Props) {
  const { site } = usePage().props;
  const head = <Head title={title ? `${title} · ${site.name}` : site.name} />;

  if (site.appearance.layout === 'top') {
    return (
      <div>
        {head}
        <header className="sticky top-0 z-10 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1.5 border-b border-hair bg-paper/86 px-gutter py-4.5 backdrop-blur-[14px]">
          <Link href={site.home_href} className="flex flex-wrap items-baseline gap-3.5 border-0 text-ink">
            <span className="font-serif text-wordmark-sm leading-[1.15]">{site.name}</span>
            <span className="hidden text-tagline tracking-[0.04em] text-ink-meta wide:inline">{site.tagline}</span>
          </Link>
          <div className="flex items-baseline gap-6">
            <Nav links={site.nav} inline />
            <ThemeToggle />
          </div>
        </header>
        <main
          className={`mx-auto max-w-[1400px] animate-page-enter px-gutter pt-block pb-section ${rail ? 'wide:grid wide:grid-cols-[minmax(0,1fr)_300px] wide:items-start wide:gap-x-section' : ''}`}
        >
          <div className="min-w-0">{children}</div>
          {rail && (
            <aside className="mt-block border-t border-hair pt-slot text-meta text-ink-muted wide:sticky wide:top-24 wide:mt-0">
              {rail}
            </aside>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="wide:flex">
      {head}
      <header className="flex flex-wrap items-baseline justify-between gap-x-5 gap-y-2 border-b border-panel-hair bg-panel px-gutter py-4 wide:sticky wide:top-0 wide:h-screen wide:w-75 wide:shrink-0 wide:flex-col wide:flex-nowrap wide:items-start wide:justify-start wide:gap-block wide:border-r wide:border-b-0 wide:px-rail-x wide:pt-block">
        <Link href={site.home_href} className="border-0 text-ink">
          <span className="block font-serif text-wordmark-sm wide:text-wordmark">{site.name}</span>
          <span className="hidden text-tagline tracking-[0.04em] text-ink-meta wide:block">{site.tagline}</span>
        </Link>
        <div className="flex items-baseline gap-4.5 wide:contents">
          <Nav links={site.nav} />
          <ThemeToggle className="wide:order-last wide:mt-auto" />
        </div>
        {rail && (
          <div className="basis-full border-t border-hair pt-slot text-meta text-ink-muted wide:basis-auto wide:self-stretch">
            {rail}
          </div>
        )}
      </header>
      <main className="min-w-0 flex-1 animate-page-enter px-gutter pt-block pb-section">{children}</main>
    </div>
  );
}
