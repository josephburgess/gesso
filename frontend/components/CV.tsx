import SectionLabel from '@/components/SectionLabel';
import type { CVGroup } from '@/types';

export default function CV({ groups, className = '' }: { groups: CVGroup[]; className?: string }) {
  return (
    <section className={`max-w-[900px] ${className}`}>
      <SectionLabel>CV</SectionLabel>
      {groups.map((group) => (
        <div key={group.label} className="mt-block">
          <h2 className="mb-3 text-title">{group.label}</h2>
          <ul className="flex flex-col gap-2 text-body-sm">
            {group.entries.map((entry, i) => (
              <li key={i} className="grid grid-cols-[3.5rem_1fr] gap-x-4">
                <span className="text-ink-meta tabular-nums">{entry.year}</span>
                <span>
                  {entry.link ? (
                    <a href={entry.link} target="_blank" rel="noopener">
                      {entry.title}
                    </a>
                  ) : (
                    <span className="text-ink">{entry.title}</span>
                  )}
                  {entry.where && <span className="text-ink-muted">, {entry.where}</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
