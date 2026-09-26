import { Link } from '@inertiajs/react';
import type { ArtworkTile } from '@/types';
import ResponsiveImage from '@/components/ResponsiveImage';

export default function GalleryTile({ tile }: { tile: ArtworkTile }) {
  return (
    <Link href={tile.href} className="group block border-0">
      <figure>
        <div className="overflow-hidden bg-image-bg">
          {tile.cover ? (
            <div className="transition-transform duration-(--d-image) ease-out group-hover:scale-(--zoom-tile)">
              <ResponsiveImage image={tile.cover} alt={tile.title} sizes="(min-width: 1000px) 30vw, 92vw" reveal />
            </div>
          ) : (
            <div className="flex aspect-4/5 items-end p-2.5">
              <span className="text-micro tracking-[0.08em] text-ink-faint uppercase">Image to come</span>
            </div>
          )}
        </div>
        <figcaption className="grid grid-cols-[1fr_auto] gap-x-3 pt-3">
          <span className="font-serif text-tile text-ink transition-colors duration-(--d-ui) ease-io group-hover:text-accent">
            {tile.title}
          </span>
          <span className={`row-span-2 self-end text-meta-sm ${tile.available ? 'text-accent' : 'text-ink-dim'}`}>
            {tile.status}
          </span>
          <span className="text-meta-sm text-ink-meta tabular-nums">{tile.year}</span>
        </figcaption>
      </figure>
    </Link>
  );
}
