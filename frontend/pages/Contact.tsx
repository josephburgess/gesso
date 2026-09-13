import { Head } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';
import type { Contact as ContactProps } from '@/types';

export default function Contact({ contact }: { contact: ContactProps }) {
  return (
    <SiteLayout>
      <Head title="Contact" />
      <h1>Contact</h1>
      {contact.details && <p className="whitespace-pre-line">{contact.details}</p>}
    </SiteLayout>
  );
}
