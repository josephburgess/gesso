import ResponsiveImage from '../../components/ResponsiveImage';
import { ArtworkDetail } from '../../types';
import SiteLayout from '../../layouts/SiteLayout';

export default function Show({ artwork }: { artwork: ArtworkDetail }) {
  const rail = (
    <>
      <h1 className="mb-1 text-title-lg">{artwork.title}</h1>
      <p className="text-meta text-ink-meta tabular-nums">{artwork.year}</p>
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
