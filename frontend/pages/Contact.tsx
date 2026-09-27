import { useForm } from '@inertiajs/react';
import SiteLayout from '@/layouts/SiteLayout';
import type { Contact as ContactProps } from '@/types';
import type { SubmitEvent } from 'react';
import Button from '@/components/Button';
import Field from '@/components/Field';
import FlashMessages from '@/components/FlashMessages';
import Honeypot from '@/components/Honeypot';
import Signup from '@/components/Signup';

export default function Contact({ contact }: { contact: ContactProps }) {
  const form = useForm({
    name: '',
    email: '',
    topic: contact.topic,
    message: '',
    website: '',
    artwork: contact.artwork?.slug ?? '',
  });

  function submit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    form.post(contact.action, { onSuccess: () => form.reset() });
  }

  return (
    <SiteLayout title="Contact">
      <h1>Contact</h1>
      {contact.details && <p className="whitespace-pre-line">{contact.details}</p>}
      <FlashMessages />
      {contact.artwork && (
        <p className="text-meta text-ink-meta">
          About <span className="font-serif text-ink">{contact.artwork.title}</span>
        </p>
      )}
      <form onSubmit={submit} className="flex max-w-190 flex-col gap-5.5 pt-9.5">
        <Field label="Name" error={form.errors.name}>
          <input
            type="text"
            required
            value={form.data.name}
            onChange={(e) => form.setData('name', e.target.value)}
            aria-invalid={!!form.errors.name}
            className="border-b input-line border-line py-2"
          />
        </Field>
        <Field label="Email" error={form.errors.email}>
          <input
            type="email"
            required
            value={form.data.email}
            onChange={(e) => form.setData('email', e.target.value)}
            aria-invalid={!!form.errors.email}
            className="border-b input-line border-line py-2"
          />
        </Field>
        <Field label="Topic" error={form.errors.topic}>
          <select
            value={form.data.topic}
            onChange={(e) => form.setData('topic', e.target.value)}
            className="cursor-pointer border-b input-line border-line py-2"
          >
            {contact.topics.map((topic) => (
              <option key={topic.value} value={topic.value}>
                {topic.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Message" error={form.errors.message}>
          <textarea
            rows={5}
            required
            value={form.data.message}
            onChange={(e) => form.setData('message', e.target.value)}
            aria-invalid={!!form.errors.message}
            className="resize-y border input-line border-line p-3 leading-[1.7]"
          />
        </Field>
        <Honeypot value={form.data.website} onChange={(value) => form.setData('website', value)} />
        <Button type="submit" disabled={form.processing} className="self-start px-6.5 py-3.25 text-[13.5px]">
          Send message
        </Button>
      </form>
      <Signup className="mt-section" />
    </SiteLayout>
  );
}
