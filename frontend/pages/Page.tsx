import SiteLayout from '@/layouts/SiteLayout';
import type { Page as PageProps } from '@/types';

export default function Page({ page }: { page: PageProps }) {
  return (
    <SiteLayout title={page.title}>
      <h1>{page.title}</h1>
      {page.blocks.map((block, i) =>
        block.heading ? (
          <h2 key={i} className="mt-block mb-2 text-title">
            {block.text}
          </h2>
        ) : (
          <p key={i} className="whitespace-pre-line">
            {block.text}
          </p>
        ),
      )}
    </SiteLayout>
  );
}
