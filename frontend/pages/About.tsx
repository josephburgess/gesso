import ResponsiveImage from '@/components/ResponsiveImage';
import SiteLayout from '@/layouts/SiteLayout';
import type { About as AboutProps, Photo } from '@/types';

function Figure({ photo, sizes, eager }: { photo: Photo; sizes: string; eager?: boolean }) {
  return (
    <figure>
      <ResponsiveImage image={photo.image} alt={photo.alt} sizes={sizes} eager={eager} className="h-auto w-full" />
      {photo.caption && <figcaption className="pt-2.5 text-meta-sm text-ink-dim">{photo.caption}</figcaption>}
    </figure>
  );
}

export default function About({ about }: { about: AboutProps }) {
  const [portrait, ...more] = about.photos;

  return (
    <SiteLayout title="About">
      <div className="mb-section flex flex-wrap items-start gap-block">
        {portrait && (
          <div className="min-w-0 flex-[1_1_280px]">
            <Figure photo={portrait} sizes="(min-width: 1000px) 30vw, 92vw" eager />
          </div>
        )}
        {about.statement && (
          <p className="mb-0 max-w-[34ch] min-w-0 flex-[999_1_380px] font-serif text-display text-ink">
            {about.statement}
          </p>
        )}
      </div>
      {about.biography.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      {more.length > 0 && (
        <div className="mt-section flex flex-wrap gap-block">
          {more.map((photo) => (
            <div key={photo.image.src} className="min-w-0 flex-[1_1_280px]">
              <Figure photo={photo} sizes="(min-width: 1000px) 30vw, 92vw" />
            </div>
          ))}
        </div>
      )}
    </SiteLayout>
  );
}
