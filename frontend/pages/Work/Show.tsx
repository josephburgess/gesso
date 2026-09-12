import ResponsiveImage from '@/components/ResponsiveImage';
import { ArtworkDetail } from '@/types';
import SiteLayout from '@/layouts/SiteLayout';

export default function Show({ artwork }: { artwork: ArtworkDetail }) {
  const rail = (
    <>
      <h1 className="mb-1 text-title-lg">{artwork.title}</h1>
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
    </SiteLayout>
  );
}
