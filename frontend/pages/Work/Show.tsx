import ResponsiveImage from '@/components/ResponsiveImage';
import { ArtworkDetail } from '@/types';
import SiteLayout from '@/layouts/SiteLayout';
import { Head } from '@inertiajs/react';

export default function Show({ artwork }: { artwork: ArtworkDetail }) {
  const rail = (
    <>
      <Head title={artwork.title} />
      <p className="text-meta text-ink-meta tabular-nums">{artwork.year}</p>
      <dl className="mt-6 flex flex-col gap-2">
        {[
          ['Medium', artwork.medium],
          ['Size', artwork.size],
        ].map(([label, value]) => (
          <div key={label} className="flex gap-3.5">
            <dt className="w-20 shrink-0 pt-0.5 text-micro tracking-[0.06em] text-ink-dim uppercase">{label}</dt>
            <dd className="text-ink-muted tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-6 flex items-baseline justify-between gap-3 text-body-sm">
        <span className="flex items-center gap-2 text-ink-muted">
          <span className={`size-2 rounded-[50%] border border-accent ${artwork.available ? 'bg-accent' : ''}`} />
          {artwork.status}
        </span>
        {artwork.price && (
          <span className="font-serif text-price leading-none text-ink tabular-nums">{artwork.price}</span>
        )}
      </div>
    </>
  );

  return (
    <SiteLayout rail={rail}>
      {artwork.cover && (
        <ResponsiveImage
          image={artwork.cover}
          alt={artwork.title}
          sizes="(min-width: 1000px) 62vw, 100vw"
          eager
          className="max-h-[85vh] w-auto"
        />
      )}
      {artwork.description.length > 0 && (
        <div className="mt-block">
          {artwork.description.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      )}
    </SiteLayout>
  );
}
