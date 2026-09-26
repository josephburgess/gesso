import { ArtworkTile } from '@/types';
import SiteLayout from '@/layouts/SiteLayout';
import GalleryTile from '@/components/GalleryTile';

export default function Index({ artworks }: { artworks: ArtworkTile[] }) {
  return (
    <SiteLayout title="Work">
      <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,250px),1fr))] items-end gap-x-grid-col gap-y-grid-row">
        {artworks.map((tile) => (
          <GalleryTile key={tile.href} tile={tile} />
        ))}
      </div>
    </SiteLayout>
  );
}
