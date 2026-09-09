import { Link } from "@inertiajs/react";

type Artwork = { title: string; year: number };

export default function Show({ artwork }: { artwork: Artwork }) {
  return (
    <>
      <h1>{artwork.title}</h1>
      <p>{artwork.year}</p>
      <Link href="/work">Back</Link>
    </>
  );
}
