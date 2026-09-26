import { Link } from '@inertiajs/react';
import ResponsiveImage from '@/components/ResponsiveImage';
import SiteLayout from '@/layouts/SiteLayout';
import type { ArtworkTile, Home as HomeProps } from '@/types';

function Status({ tile }: { tile: ArtworkTile }) {
  return <span className={tile.available ? 'text-accent' : 'text-ink-dim'}>{tile.status}</span>;
}

export default function Home({ home }: { home: HomeProps }) {
  const [lead, ...pair] = home.featured;

  const rail = (
    <div className="flex flex-col gap-5.5">
      {home.intro && <p className="mb-0 max-w-[33ch] text-[13.5px] leading-[1.75]">{home.intro}</p>}
      <Link href={home.about_href} className="self-start text-meta">
        Read the full statement
      </Link>
    </div>
  );

  return (
    <SiteLayout rail={rail}>
      {lead && (
        <>
          <div className="text-label text-ink-faint uppercase">Selected work</div>
          <Link href={lead.href} className="mt-6.5 block border-0">
            <figure>
              {lead.cover && (
                <ResponsiveImage image={lead.cover} alt={lead.title} sizes="(min-width: 861px) 70vw, 92vw" eager />
              )}
              <figcaption className="flex flex-wrap items-baseline justify-between gap-x-5.5 gap-y-2 pt-4">
                <span className="font-serif text-title-lg text-ink">{lead.title}</span>
                <span className="flex flex-wrap gap-4.5 text-meta text-ink-meta">
                  <span>{lead.year}</span>
                  <span>{lead.medium}</span>
                  <span className="tabular-nums">{lead.size}</span>
                  <Status tile={lead} />
                </span>
              </figcaption>
            </figure>
          </Link>
        </>
      )}

      {pair.length > 0 && (
        <div className="flex flex-wrap items-end gap-grid-col pt-section">
          {pair.map((tile, i) => (
            <Link
              key={tile.href}
              href={tile.href}
              className={`block min-w-0 border-0 ${i === 0 ? 'flex-[1_1_300px]' : 'mb-block max-w-[44%] flex-[1_1_220px]'}`}
            >
              <figure>
                {tile.cover && (
                  <ResponsiveImage image={tile.cover} alt={tile.title} sizes="(min-width: 861px) 35vw, 92vw" />
                )}
                <figcaption className="flex items-baseline justify-between gap-3.5 pt-3 text-meta-sm text-ink-meta">
                  <span>
                    <span className="font-serif text-title text-ink">{tile.title}</span> · {tile.year}
                  </span>
                  <Status tile={tile} />
                </figcaption>
              </figure>
            </Link>
          ))}
        </div>
      )}

      {home.statement && <p className="mt-section max-w-[30ch] font-serif text-display text-ink">{home.statement}</p>}

      {home.index.length > 0 && (
        <section className="mt-section">
          <div className="flex items-baseline justify-between border-b border-rule pb-2.5 text-label uppercase">
            <span>Index of works</span>
            <span className="text-ink-dim tabular-nums">{String(home.index.length).padStart(2, '0')}</span>
          </div>
          {home.index.map((tile, i) => (
            <Link
              key={tile.href}
              href={tile.href}
              className="grid grid-cols-[26px_minmax(0,1fr)_44px_auto] items-baseline gap-x-3.5 border-b border-hair-light px-1 py-3.25 text-meta-sm text-ink-meta hover:bg-accent-tint wide:grid-cols-[26px_minmax(0,1.1fr)_44px_minmax(0,1.2fr)_104px]"
            >
              <span className="text-micro text-ink-faint tabular-nums">{String(i + 1).padStart(2, '0')}</span>
              <span className="truncate font-serif text-title text-ink">{tile.title}</span>
              <span className="tabular-nums">{tile.year}</span>
              <span className="hidden truncate wide:block">{tile.medium}</span>
              <Status tile={tile} />
            </Link>
          ))}
        </section>
      )}
    </SiteLayout>
  );
}
