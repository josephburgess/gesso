import { Head, Link, usePage } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';

export default function NotFound() {
  const { site } = usePage().props;

  return (
    <SiteLayout>
      <Head title="Page not found" />
      <h1>Page not found</h1>
      <p>This page doesn't exist, or the work has been taken down.</p>
      <Link href={site.home_href}>Back to the home page</Link>
    </SiteLayout>
  );
}
