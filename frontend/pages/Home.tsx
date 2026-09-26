import { Link, usePage } from '@inertiajs/react';
import { useRef, type Ref } from 'react';
import Figure from '@/components/Figure';
import IndexOfWorks from '@/components/IndexOfWorks';
import ResponsiveImage from '@/components/ResponsiveImage';
import Reveal from '@/components/Reveal';
import SectionLabel from '@/components/SectionLabel';
import Signup from '@/components/Signup';
import Statement from '@/components/Statement';
import Status from '@/components/Status';
import Zoom from '@/components/Zoom';
import useFitHeight from '@/hooks/useFitHeight';
import useUltrawide from '@/hooks/useUltrawide';
import SiteLayout from '@/layouts/SiteLayout';
import type { ArtworkTile, Home as HomeProps } from '@/types';

const ratio = (tile: ArtworkTile) => (tile.cover ? tile.cover.width / tile.cover.height : 1);

const fitWidth = (height: number | null, tile: ArtworkTile, scale = 1) =>
  height && tile.cover ? `min(100%, ${Math.round(height * scale * ratio(tile))}px)` : '100%';

function Caption({ tile, large, ref }: { tile: ArtworkTile; large?: boolean; ref?: Ref<HTMLDivElement> }) {
  return (
    <div ref={ref} className="flex flex-wrap items-baseline justify-between gap-x-5.5 gap-y-1.5 pt-4">
      <span className={`font-serif text-ink ${large ? 'text-title-lg' : 'text-title'}`}>{tile.title}</span>
      <span className="flex flex-wrap gap-4.5 text-meta text-ink-meta">
        <span>{tile.year}</span>
        <span>{tile.medium}</span>
        <span className="tabular-nums">{tile.size}</span>
        <Status status={tile.status} available={tile.available} />
      </span>
    </div>
  );
}

function Work({ tile, sizes, eager }: { tile: ArtworkTile; sizes: string; eager?: boolean }) {
  return (
    tile.cover && (
      <Zoom>
        <ResponsiveImage image={tile.cover} alt={tile.title} sizes={sizes} eager={eager} reveal className="w-full" />
      </Zoom>
    )
  );
}

export default function Home({ home }: { home: HomeProps }) {
  const { site } = usePage().props;
  const [lead, second] = home.featured;
  const top = site.appearance.layout === 'top';
  const ultrawide = useUltrawide();
  const hero = useRef<HTMLDivElement>(null);
  const caption = useRef<HTMLDivElement>(null);
  const fitHeight = useFitHeight(hero, caption);

  const rail = !top && (
    <div className="flex flex-col gap-5.5">
      {home.intro && <p className="mb-0 max-w-[33ch] text-[13.5px] leading-[1.75]">{home.intro}</p>}
      <Link href={home.about_href} className="self-start text-meta">
        Read the full statement
      </Link>
    </div>
  );

  return (
    <SiteLayout rail={rail}>
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <SectionLabel>Selected work</SectionLabel>
        {top && home.intro && (
          <p className="mb-0 max-w-[46ch] text-[13.5px] leading-[1.75] text-ink-muted">{home.intro}</p>
        )}
      </div>

      {lead && (
        <div ref={hero} className={`mt-6.5 ${ultrawide ? 'flex items-end justify-center gap-section' : ''}`}>
          <Link
            href={lead.href}
            style={{ width: fitWidth(fitHeight, lead) }}
            className={`block shrink-0 border-0 ${ultrawide ? '' : 'mx-auto'}`}
          >
            <Work tile={lead} sizes="(min-width: 861px) 70vw, 92vw" eager />
            <Caption tile={lead} large ref={caption} />
          </Link>
          {ultrawide && (
            <div className="flex min-w-60 flex-[0_1_420px] flex-col gap-block">
              {home.statement && <Statement className="max-w-[20ch]">{home.statement}</Statement>}
              {second && (
                <Link
                  href={second.href}
                  style={{ width: fitWidth(fitHeight, second, 0.55) }}
                  className="block border-0"
                >
                  <Work tile={second} sizes="420px" />
                  <Caption tile={second} />
                </Link>
              )}
            </div>
          )}
        </div>
      )}

      {!ultrawide && (second || home.statement) && (
        <div className="mt-section flex flex-wrap items-end gap-section">
          {second && (
            <Reveal className="max-w-[620px] min-w-0 flex-[1_1_320px]">
              <Link href={second.href} className="block border-0">
                <Work tile={second} sizes="(min-width: 861px) 45vw, 92vw" />
                <Caption tile={second} />
              </Link>
            </Reveal>
          )}
          {home.statement && (
            <Reveal delay={120} className="min-w-0 flex-[1_1_300px] pb-block">
              <Statement className="max-w-[22ch]">{home.statement}</Statement>
            </Reveal>
          )}
        </div>
      )}

      {home.process.length > 0 && (
        <section className="mt-section">
          <Reveal>
            <SectionLabel>In the studio</SectionLabel>
          </Reveal>
          <div className="mt-6.5 flex flex-wrap items-end gap-grid-col">
            {home.process.map((photo, i) => (
              <Reveal
                key={photo.image.src}
                delay={i * 120}
                className={`min-w-0 ${i === 0 ? 'max-w-[380px] flex-[1_1_240px]' : 'max-w-[520px] flex-[1.4_1_300px]'}`}
              >
                <Figure
                  image={photo.image}
                  alt={photo.caption || `${photo.title} in the studio`}
                  caption={[photo.caption, photo.title].filter(Boolean).join(' · ')}
                  sizes="(min-width: 861px) 35vw, 92vw"
                />
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {site.appearance.show_index && home.index.length > 0 && (
        <Reveal className="mt-section">
          <IndexOfWorks works={home.index} />
        </Reveal>
      )}
      <Reveal className="mt-section">
        <Signup />
      </Reveal>
    </SiteLayout>
  );
}
