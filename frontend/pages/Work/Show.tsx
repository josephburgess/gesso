import { Link } from '@inertiajs/react';

type Artwork = { title: string; year: number; cover: string | null };

export default function Show({ artwork }: { artwork: Artwork }) {
  return (
    <>
      {artwork.cover && <img src={artwork.cover} alt={artwork.title} style={{ maxWidth: '100%' }} />}
      <h1>{artwork.title}</h1>
      <p>{artwork.year}</p>
      <Link href="/work">Back</Link>
    </>
  );
}
