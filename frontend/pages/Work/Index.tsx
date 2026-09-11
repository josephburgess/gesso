import { Link } from '@inertiajs/react';
import ResponsiveImage from '../../components/ResponsiveImage';
import { ImageProps } from '../../types';

type Tile = { title: string; year: number; href: string; cover: ImageProps | null };

export default function Index({ artworks }: { artworks: Tile[] }) {
  return (
    <ul>
      {artworks.map((a) => (
        <li key={a.href}>
          <Link href={a.href}>
            {a.cover && <ResponsiveImage image={a.cover} alt={a.title} sizes="240px" />}
            {a.title}
          </Link>{' '}
          ({a.year})
        </li>
      ))}
    </ul>
  );
}
