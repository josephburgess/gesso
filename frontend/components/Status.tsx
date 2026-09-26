export default function Status({ status, available }: { status: string; available: boolean }) {
  return <span className={available ? 'text-accent' : 'text-ink-dim'}>{status}</span>;
}
