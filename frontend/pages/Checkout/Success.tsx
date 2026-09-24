import { Head } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';

export default function Success({ title }: { title: string | null }) {
  return (
    <SiteLayout>
      <Head title="Thank you" />
      <h1>Thank you</h1>
      <p>
        {title ? (
          <>
            Your order for <span className="font-serif text-ink">{title}</span> is confirmed.
          </>
        ) : (
          'Your order is confirmed.'
        )}{' '}
        A confirmation email is on its way, and we'll be in touch about delivery.
      </p>
    </SiteLayout>
  );
}
