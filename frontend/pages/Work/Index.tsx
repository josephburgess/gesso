import { Link } from '@inertiajs/react';

type Tile = { title: string; year: number; href: string; cover: string | null };

export default function Index({ artworks }: { artworks: Tile[] }) {
  return (
    <ul>
      {artworks.map((a) => (
        <li key={a.href}>
          <Link href={a.href}>
            {a.cover && <img src={a.cover} alt={a.title} width={240} />}
            {a.title}
          </Link>{' '}
          ({a.year})
        </li>
      ))}
    </ul>
  );
}
