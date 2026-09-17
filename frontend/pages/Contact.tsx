import { Head, useForm, usePage } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';
import type { Contact as ContactProps } from '@/types';
import type { SubmitEvent } from 'react';
import Field from '@/components/Field';

const line =
  'bg-transparent text-body-sm text-ink outline-none transition-colors duration-(--d-state) focus:border-accent';

export default function Contact({ contact }: { contact: ContactProps }) {
  const { flash } = usePage();
  const form = useForm({ name: '', email: '', message: '', website: '' });

  function submit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    form.post(contact.action, { onSuccess: () => form.reset() });
  }

  return (
    <SiteLayout>
      <Head title="Contact" />
      <h1>Contact</h1>
      {contact.details && <p className="whitespace-pre-line">{contact.details}</p>}
      {flash.messages?.map((m, i) => (
        <p key={i} role="status" className="text-ink">
          {m.message}
        </p>
      ))}
      <form onSubmit={submit} className="flex max-w-[760px] flex-col gap-5.5 pt-9.5">
        <div className="flex flex-wrap gap-5.5">
          <Field label="Name" error={form.errors.name} className="min-w-0 flex-[1_1_220px]">
            <input
              type="text"
              required
              value={form.data.name}
              onChange={(e) => form.setData('name', e.target.value)}
              aria-invalid={!!form.errors.name}
              className={`border-b border-line py-2 ${line}`}
            />
          </Field>
          <Field label="Email" error={form.errors.email} className="min-w-0 flex-[1_1_220px]">
            <input
              type="email"
              required
              value={form.data.email}
              onChange={(e) => form.setData('email', e.target.value)}
              aria-invalid={!!form.errors.email}
              className={`border-b border-line py-2 ${line}`}
            />
          </Field>
        </div>
        <Field label="Message" error={form.errors.message}>
          <textarea
            rows={5}
            required
            value={form.data.message}
            onChange={(e) => form.setData('message', e.target.value)}
            aria-invalid={!!form.errors.message}
            className={`resize-y border border-line p-3 leading-[1.7] ${line}`}
          />
        </Field>
        <input
          type="text"
          name="website"
          tabIndex={-1}
          autoComplete="off"
          aria-hidden="true"
          value={form.data.website}
          onChange={(e) => form.setData('website', e.target.value)}
          className="absolute -left-[9999px]"
        />
        <button
          type="submit"
          disabled={form.processing}
          className="self-start bg-ink px-6.5 py-3.25 text-[13.5px] tracking-[0.03em] text-paper transition-colors duration-(--d-state) hover:bg-accent disabled:opacity-60"
        >
          Send message
        </button>
      </form>
    </SiteLayout>
  );
}
