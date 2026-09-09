import { Link } from "@inertiajs/react";

type Tile = { title: string; year: number; href: string };

export default function Index({ artworks }: { artworks: Tile[] }) {
  return (
    <ul>
      {artworks.map((a) => (
        <li key={a.href}>
          <Link href={a.href}>{a.title}</Link> ({a.year})
        </li>
      ))}
    </ul>
  );
}
