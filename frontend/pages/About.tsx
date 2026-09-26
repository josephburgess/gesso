import { usePage } from '@inertiajs/react';
import Figure from '@/components/Figure';
import Reveal from '@/components/Reveal';
import Statement from '@/components/Statement';
import SiteLayout from '@/layouts/SiteLayout';
import type { About as AboutProps } from '@/types';

export default function About({ about }: { about: AboutProps }) {
  const { site } = usePage().props;
  const above = site.appearance.about_layout === 'above';
  const [portrait, ...more] = about.photos;

  return (
    <SiteLayout title="About">
      <div className={`mb-section flex gap-x-section gap-y-block ${above ? 'flex-col' : 'flex-wrap items-end'}`}>
        {portrait && (
          <div className={`min-w-0 ${above ? 'max-w-[900px]' : 'max-w-[560px] flex-[1_1_300px]'}`}>
            <Figure
              image={portrait.image}
              alt={portrait.alt}
              caption={portrait.caption}
              sizes={above ? '(min-width: 1000px) 900px, 92vw' : '(min-width: 1000px) 40vw, 92vw'}
              eager
            />
          </div>
        )}
        {about.statement && (
          <Reveal className={`min-w-0 ${above ? '' : 'flex-[999_1_340px]'}`}>
            <Statement className="max-w-[26ch]">{about.statement}</Statement>
          </Reveal>
        )}
      </div>
      {about.biography.length > 0 && (
        <Reveal className="max-w-[900px] gap-section [column-width:340px]">
          {about.biography.map((p, i) => (
            <p key={i} className="break-inside-avoid">
              {p}
            </p>
          ))}
        </Reveal>
      )}
      {more.length > 0 && (
        <div className="mt-section flex flex-wrap gap-block">
          {more.map((photo) => (
            <Reveal key={photo.image.src} className="max-w-[420px] min-w-0 flex-[1_1_280px]">
              <Figure
                image={photo.image}
                alt={photo.alt}
                caption={photo.caption}
                sizes="(min-width: 1000px) 30vw, 92vw"
              />
            </Reveal>
          ))}
        </div>
      )}
    </SiteLayout>
  );
}
