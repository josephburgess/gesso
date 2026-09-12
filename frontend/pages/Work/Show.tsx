import { Link } from '@inertiajs/react';
import ResponsiveImage from '../../components/ResponsiveImage';
import { ArtworkDetail } from '../../types';
import SiteLayout from '../../layouts/SiteLayout';

export default function Show({ artwork }: { artwork: ArtworkDetail }) {
  return (
    <SiteLayout>
      {artwork.cover && <ResponsiveImage image={artwork.cover} alt={artwork.title} sizes="100vw" eager />}
      <h1>{artwork.title}</h1>
      <p>{artwork.year}</p>
      <Link href="/work">Back</Link>
    </SiteLayout>
  );
}
