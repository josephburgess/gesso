import { Link, usePage } from '@inertiajs/react';
import { useState, type SubmitEvent } from 'react';
import Button from '@/components/Button';
import Honeypot from '@/components/Honeypot';
import SectionLabel from '@/components/SectionLabel';

const csrfToken = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? '';

type Props = { label?: string; text?: string; className?: string };

export default function Signup({
  label = 'Mailing list',
  text = 'Occasional emails about new work. Unsubscribe any time.',
  className = '',
}: Props) {
  const { site } = usePage().props;
  const [email, setEmail] = useState('');
  const [website, setWebsite] = useState('');
  const [error, setError] = useState('');
  const [thanks, setThanks] = useState('');
  const [sending, setSending] = useState(false);

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSending(true);
    setError('');
    try {
      const response = await fetch(site.subscribe_href, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ email, website }),
      });
      const body = await response.json();
      if (response.ok) setThanks(body.message);
      else setError(body.errors?.email ?? 'Something went wrong. Please try again.');
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setSending(false);
    }
  }

  return (
    <section className={`max-w-[620px] border border-line bg-panel p-block ${className}`}>
      <SectionLabel>{label}</SectionLabel>
      <p className="mt-3 mb-0 max-w-[46ch] text-meta text-ink-muted">
        {text}
        {site.privacy_href && (
          <>
            {' '}
            <Link href={site.privacy_href}>How we use your email</Link>
          </>
        )}
      </p>
      {thanks ? (
        <p role="status" className="mt-4 mb-0 text-body-sm text-ink">
          {thanks}
        </p>
      ) : (
        <form onSubmit={submit} className="mt-4 flex max-w-[460px] flex-wrap items-end gap-3">
          <label className="flex min-w-0 flex-[1_1_220px] flex-col gap-1.75">
            <span className="sr-only">Email</span>
            <input
              type="email"
              required
              placeholder="Your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={!!error}
              className="border-b input-line border-line py-2 placeholder:text-ink-faint"
            />
          </label>
          <Honeypot value={website} onChange={setWebsite} />
          <Button type="submit" disabled={sending} className="cursor-pointer px-5 py-2.5 text-[13.5px]">
            Sign up
          </Button>
          {error && <span className="basis-full text-meta-sm text-accent">{error}</span>}
        </form>
      )}
    </section>
  );
}
