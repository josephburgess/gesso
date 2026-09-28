import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';

type Props = { delay?: number; className?: string; style?: CSSProperties; children: ReactNode };

export default function Reveal({ delay = 0, className = '', style, children }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        setShown(true);
        observer.disconnect();
      },
      { rootMargin: '0px 0px -6% 0px' },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ ...style, transitionDelay: `${delay}ms` }}
      className={`transition-reveal ${shown ? 'opacity-100' : 'translate-y-3.5 opacity-0'} ${className}`}
    >
      {children}
    </div>
  );
}
