import Lightbox from '@/components/Lightbox';
import ResponsiveImage from '@/components/ResponsiveImage';
import type { ArtworkDetail, Purchase } from '@/types';
import SiteLayout from '@/layouts/SiteLayout';
import { Link, useForm, usePage } from '@inertiajs/react';
import { useState } from 'react';

function PurchasePanel({ purchase }: { purchase: Purchase }) {
  const { flash } = usePage();
  const checkout = useForm({});

  return (
    <div className="mt-6 flex flex-col gap-2.25">
      {flash.messages?.map((m, i) => (
        <p key={i} role="status" className="text-body-sm text-ink">
          {m.message}
        </p>
      ))}
      {purchase.action && (
        <button
          type="button"
          disabled={checkout.processing}
          onClick={() => checkout.post(purchase.action!)}
          className="bg-ink px-4.5 py-3.25 text-center text-body-sm tracking-[0.03em] text-paper transition-colors duration-(--d-state) hover:bg-accent active:translate-y-px disabled:opacity-60"
        >
          Purchase
        </button>
      )}
      <Link
        href={purchase.enquire_href}
        className="border border-line px-4.5 py-3 text-center text-body-sm transition-colors duration-(--d-state) hover:border-ink hover:bg-accent-tint"
      >
        {purchase.enquire_label}
      </Link>
      {purchase.note && <p className="pt-0.5 text-meta-sm text-ink-dim">{purchase.note}</p>}
    </div>
  );
}

export default function Show({ artwork, purchase }: { artwork: ArtworkDetail; purchase: Purchase }) {
  const [open, setOpen] = useState<number | null>(null);
  const [first, ...rest] = artwork.images;
  const alt = (index: number) =>
    artwork.images.length > 1 ? `${artwork.title}, image ${index + 1} of ${artwork.images.length}` : artwork.title;

  const rail = (
    <>
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
      <PurchasePanel purchase={purchase} />
    </>
  );

  return (
    <SiteLayout title={artwork.title} rail={rail}>
      {first && (
        <button type="button" aria-label="View larger" onClick={() => setOpen(0)} className="block cursor-zoom-in">
          <ResponsiveImage
            image={first}
            alt={alt(0)}
            sizes="(min-width: 1000px) 62vw, 100vw"
            eager
            className="max-h-[85vh] w-auto"
          />
        </button>
      )}
      {rest.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-3">
          {rest.map((image, i) => (
            <button
              key={image.src}
              type="button"
              aria-label="View larger"
              onClick={() => setOpen(i + 1)}
              className="cursor-zoom-in"
            >
              <ResponsiveImage image={image} alt={alt(i + 1)} sizes="160px" className="h-28 w-auto" />
            </button>
          ))}
        </div>
      )}
      <Lightbox images={artwork.images} index={open} alt={alt} onChange={setOpen} />
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
