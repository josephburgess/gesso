import { usePage } from '@inertiajs/react';

export default function FlashMessages({ className = '' }: { className?: string }) {
  const { flash } = usePage();

  return flash.messages?.map((m, i) => (
    <p key={i} role="status" className={`text-ink ${className}`}>
      {m.message}
    </p>
  ));
}
