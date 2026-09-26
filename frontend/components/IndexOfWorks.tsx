import { Link } from '@inertiajs/react';
import { useRef, useState } from 'react';
import Status from '@/components/Status';
import type { ArtworkTile } from '@/types';

const pad = (n: number) => String(n).padStart(2, '0');

export default function IndexOfWorks({ works }: { works: ArtworkTile[] }) {
  const section = useRef<HTMLElement>(null);
  const [hovered, setHovered] = useState<ArtworkTile | null>(null);
  const [y, setY] = useState(0);
  const thumb = hovered?.cover?.thumb;

  return (
    <section
      ref={section}
      className="relative"
      onMouseMove={(event) => setY(event.clientY - (section.current?.getBoundingClientRect().top ?? 0))}
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
      <div
        aria-hidden="true"
        style={{ top: y, transitionDuration: 'var(--d-state), calc(var(--d-state) * 0.6)' }}
        className={`pointer-events-none absolute right-[90px] z-2 w-[150px] -translate-y-1/2 transition-[opacity,top] ease-out wide:right-[150px] ${thumb ? 'opacity-100' : 'opacity-0'}`}
      >
        {thumb && <img src={thumb} alt="" className="w-full" />}
      </div>
    </section>
  );
}
