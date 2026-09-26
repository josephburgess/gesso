import { usePage } from '@inertiajs/react';
import { useState, type SubmitEvent } from 'react';
import SectionLabel from '@/components/SectionLabel';

const csrfToken = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? '';

export default function Signup({ className = '' }: { className?: string }) {
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
    <section className={className}>
      <SectionLabel>Mailing list</SectionLabel>
      <p className="mt-3 mb-0 max-w-[46ch] text-meta text-ink-muted">
        Occasional emails about new work. Unsubscribe any time.
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
              className="border-b border-line bg-transparent py-2 text-body-sm text-ink transition-colors duration-(--d-state) outline-none placeholder:text-ink-faint focus:border-accent"
            />
          </label>
          <input
            type="text"
            name="website"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            className="absolute left-[9999px]"
          />
          <button
            type="submit"
            disabled={sending}
            className="cursor-pointer bg-ink px-5 py-2.5 text-[13.5px] tracking-[0.03em] text-paper transition-colors duration-(--d-state) hover:bg-accent disabled:opacity-60"
          >
            Sign up
          </button>
          {error && <span className="basis-full text-meta-sm text-accent">{error}</span>}
        </form>
      )}
    </section>
  );
}
