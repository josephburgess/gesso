import { Link, usePage } from '@inertiajs/react';
import type { ArtworkTile } from '@/types';
import SiteLayout from '@/layouts/SiteLayout';
import GalleryTile from '@/components/GalleryTile';
import ResponsiveImage from '@/components/ResponsiveImage';
import Reveal from '@/components/Reveal';
import Status from '@/components/Status';
import Zoom from '@/components/Zoom';

function Tile({ tile, i }: { tile: ArtworkTile; i: number }) {
  return (
    <Reveal delay={(i % 3) * 90}>
      <GalleryTile tile={tile} />
    </Reveal>
  );
}

function Exhibit({ tile, i }: { tile: ArtworkTile; i: number }) {
  const ratio = tile.cover ? tile.cover.width / tile.cover.height : 1;

  return (
    <Reveal>
      <div className={`flex flex-wrap items-end gap-x-section gap-y-block ${i % 2 ? 'wide:flex-row-reverse' : ''}`}>
        <Link
          href={tile.href}
          style={{ maxWidth: `calc(72vh * ${ratio})` }}
          className="min-w-0 flex-[1_1_340px] border-0"
        >
          {tile.cover && (
            <Zoom>
              <ResponsiveImage
                image={tile.cover}
                alt={tile.title}
                sizes="(min-width: 861px) 55vw, 92vw"
                reveal
                className="w-full"
              />
            </Zoom>
          )}
        </Link>
        <div className="flex min-w-0 flex-[0_1_280px] flex-col gap-2.5">
          <span className="text-micro text-ink-faint tabular-nums">{String(i + 1).padStart(2, '0')}</span>
          <span className="font-serif text-h2 leading-tight text-ink">{tile.title}</span>
          <span className="text-meta text-ink-meta">
            {tile.year} · {tile.medium}
            <br />
            <span className="tabular-nums">{tile.size}</span>
          </span>
          <span className="flex items-baseline gap-4.5 text-meta">
            <Status status={tile.status} available={tile.available} />
            {tile.available && tile.price && (
              <span className="font-serif text-title text-ink tabular-nums">{tile.price}</span>
            )}
          </span>
          <Link href={tile.href} className="mt-1.5 self-start text-meta">
            View work
          </Link>
        </div>
      </div>
    </Reveal>
  );
}

export default function Index({ artworks }: { artworks: ArtworkTile[] }) {
  const { site } = usePage().props;
  const layout = site.appearance.work_layout;

  return (
    <SiteLayout title="Work">
      {layout === 'stack' && (
        <div className="flex flex-col gap-section">
          {artworks.map((tile, i) => (
            <Exhibit key={tile.href} tile={tile} i={i} />
          ))}
        </div>
      )}
      {layout === 'salon' && (
        <div className="columns-3 gap-grid-col [column-width:240px]">
          {artworks.map((tile, i) => (
            <div key={tile.href} className="mb-grid-row break-inside-avoid">
              <Tile tile={tile} i={i} />
            </div>
          ))}
        </div>
      )}
      {layout === 'grid' && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,250px),1fr))] items-end gap-x-grid-col gap-y-grid-row">
          {artworks.map((tile, i) => (
            <Tile key={tile.href} tile={tile} i={i} />
          ))}
        </div>
      )}
    </SiteLayout>
  );
}
