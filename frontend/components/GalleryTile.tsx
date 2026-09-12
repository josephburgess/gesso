import { Link } from '@inertiajs/react';
import type { ArtworkTile } from '../types';
import ResponsiveImage from './ResponsiveImage';

export default function GalleryTile({ tile }: { tile: ArtworkTile }) {
  return (
    <Link href={tile.href} className="block border-0">
      <figure>
        {tile.cover && <ResponsiveImage image={tile.cover} alt={tile.title} sizes="(min-width: 1000px) 30vw, 92vw" />}
        <figcaption className="flex items-baseline justify-between gap-3 pt-3">
          <span className="font-serif text-tile text-ink">{tile.title}</span>
          <span className="text-meta-sm text-ink-meta tabular-nums">{tile.year}</span>
        </figcaption>
      </figure>
    </Link>
  );
}
