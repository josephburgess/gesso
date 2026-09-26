import { useLayoutEffect, useState, type RefObject } from 'react';

export default function useFitHeight(hero: RefObject<HTMLElement | null>, caption: RefObject<HTMLElement | null>) {
  const [height, setHeight] = useState<number | null>(null);

  useLayoutEffect(() => {
    function measure() {
      if (!hero.current) return;
      const top = hero.current.getBoundingClientRect().top + window.scrollY;
      const next = Math.max(240, window.innerHeight - top - (caption.current?.offsetHeight ?? 60) - 24);
      setHeight((prev) => (prev !== null && Math.abs(prev - next) < 2 ? prev : next));
    }
    measure();
    const observer = new ResizeObserver(measure);
    if (caption.current) observer.observe(caption.current);
    window.addEventListener('resize', measure);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', measure);
    };
  }, [hero, caption]);

  return height;
}
