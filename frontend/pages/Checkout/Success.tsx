import { Link } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';

export default function Success({ title, work_href }: { title: string | null; work_href: string }) {
  return (
    <SiteLayout title="Thank you">
      <h1>Thank you</h1>
      <p>
        {title ? (
          <>
            Your order for <span className="work-title font-serif text-ink">{title}</span> is confirmed.
          </>
        ) : (
          'Your order is confirmed.'
        )}{' '}
        A confirmation email is on its way, and we'll be in touch about delivery.
      </p>
      <Link href={work_href} className="text-meta">
        Back to the work
      </Link>
    </SiteLayout>
  );
}
