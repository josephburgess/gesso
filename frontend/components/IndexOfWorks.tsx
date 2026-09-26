import { Link } from '@inertiajs/react';
import { useState } from 'react';
import { createPortal } from 'react-dom';
import Status from '@/components/Status';
import type { ArtworkTile } from '@/types';

const pad = (n: number) => String(n).padStart(2, '0');

const PREVIEW_WIDTH = 150;
const OFFSET = 18;

export default function IndexOfWorks({ works }: { works: ArtworkTile[] }) {
  const [hovered, setHovered] = useState<ArtworkTile | null>(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const cover = hovered?.cover;
  const height = cover ? (PREVIEW_WIDTH * cover.height) / cover.width : 0;
  const left = Math.min(pointer.x + OFFSET, window.innerWidth - PREVIEW_WIDTH - OFFSET);
  const top = pointer.y + OFFSET + height > window.innerHeight ? pointer.y - OFFSET - height : pointer.y + OFFSET;

  return (
    <section
      onMouseMove={(event) => setPointer({ x: event.clientX, y: event.clientY })}
      onMouseLeave={() => setHovered(null)}
    >
      <div className="flex items-baseline justify-between border-b border-rule pb-2.5 text-label uppercase">
        <span>Index of works</span>
        <span className="text-ink-dim tabular-nums">{pad(works.length)}</span>
      </div>
      {works.map((tile, i) => (
        <Link
          key={tile.href}
          href={tile.href}
          onMouseEnter={() => setHovered(tile)}
          className="grid grid-cols-[26px_minmax(0,1fr)_44px_auto] items-baseline gap-x-3.5 border-b border-hair-light px-1 py-3.25 text-meta-sm text-ink-meta transition-colors duration-(--d-ui) ease-io hover:bg-accent-tint wide:grid-cols-[26px_minmax(0,1.1fr)_44px_minmax(0,1.2fr)_104px]"
        >
          <span className="text-micro text-ink-faint tabular-nums">{pad(i + 1)}</span>
          <span className="truncate font-serif text-title text-ink">{tile.title}</span>
          <span className="tabular-nums">{tile.year}</span>
          <span className="hidden truncate wide:block">{tile.medium}</span>
          <Status status={tile.status} available={tile.available} />
        </Link>
      ))}
      {createPortal(
        <div
          aria-hidden="true"
          style={{ left, top, width: PREVIEW_WIDTH }}
          className={`pointer-events-none fixed z-2 transition-opacity duration-(--d-state) ease-out ${cover ? 'opacity-100' : 'opacity-0'}`}
        >
          {cover && (
            <img
              src={cover.thumb}
              alt=""
              width={cover.width}
              height={cover.height}
              className="w-full border-4 border-[#fff]"
            />
          )}
        </div>,
        document.body,
      )}
    </section>
  );
}
