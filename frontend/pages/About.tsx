import SiteLayout from '@/layouts/SiteLayout';
import type { About as AboutProps } from '@/types';

export default function About({ about }: { about: AboutProps }) {
  return (
    <SiteLayout title="About">
      {about.statement && <p className="mb-section max-w-[34ch] font-serif text-display text-ink">{about.statement}</p>}
      {about.biography.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </SiteLayout>
  );
}
