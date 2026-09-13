import { Link } from '@inertiajs/react';
import type { ArtworkTile } from '@/types';
import ResponsiveImage from '@/components/ResponsiveImage';

export default function GalleryTile({ tile }: { tile: ArtworkTile }) {
  return (
    <Link href={tile.href} className="block border-0">
      <figure>
        {tile.cover && <ResponsiveImage image={tile.cover} alt={tile.title} sizes="(min-width: 1000px) 30vw, 92vw" />}
        <figcaption className="grid grid-cols-[1fr_auto] gap-x-3 pt-3">
          <span className="font-serif text-tile text-ink">{tile.title}</span>
          <span className={`row-span-2 self-end text-meta-sm ${tile.available ? 'text-accent' : 'text-ink-dim'}`}>
            {tile.status}
          </span>
          <span className="text-meta-sm text-ink-meta tabular-nums">{tile.year}</span>
        </figcaption>
      </figure>
    </Link>
  );
}
