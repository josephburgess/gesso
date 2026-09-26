import { useEffect, useRef } from 'react';
import type { ImageProps } from '@/types';

type Props = {
  images: ImageProps[];
  index: number | null;
  alt: (index: number) => string;
  onChange: (index: number | null) => void;
};

const control =
  'absolute flex size-11 items-center justify-center text-on-overlay/80 transition-colors duration-(--d-state) hover:text-on-overlay';

export default function Lightbox({ images, index, alt, onChange }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const touchStart = useRef<number | null>(null);
  const count = images.length;

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (index === null && element.open) element.close();
    if (index !== null && !element.open) element.showModal();
  }, [index]);

  useEffect(() => {
    if (index === null || count < 2) return;
    function onKeyDown(event: KeyboardEvent) {
      if (index === null) return;
      if (event.key === 'ArrowRight') onChange((index + 1) % count);
      if (event.key === 'ArrowLeft') onChange((index - 1 + count) % count);
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [index, count, onChange]);

  function step(by: number) {
    if (index !== null) onChange((index + by + count) % count);
  }

  const image = index === null ? null : images[index];

  return (
    <dialog
      ref={dialog}
      onClose={() => onChange(null)}
      className="m-0 h-dvh max-h-none w-dvw max-w-none bg-transparent p-0 backdrop:bg-overlay/90"
    >
      <div
        className="flex h-full w-full items-center justify-center p-4 wide:p-12"
        onClick={(event) => event.target === event.currentTarget && dialog.current?.close()}
        onTouchStart={(event) => (touchStart.current = event.touches[0].clientX)}
        onTouchEnd={(event) => {
          if (touchStart.current === null || count < 2) return;
          const distance = event.changedTouches[0].clientX - touchStart.current;
          if (Math.abs(distance) > 50) step(distance < 0 ? 1 : -1);
          touchStart.current = null;
        }}
      >
        {image && index !== null && (
          <img
            src={image.src}
            srcSet={image.srcset}
            sizes="100vw"
            width={image.width}
            height={image.height}
            alt={alt(index)}
            className="max-h-full max-w-full object-contain"
          />
        )}
        <button
          type="button"
          aria-label="Close"
          onClick={() => dialog.current?.close()}
          className={`${control} top-2 right-2 text-2xl`}
        >
          ×
        </button>
        {count > 1 && (
          <>
            <button
              type="button"
              aria-label="Previous image"
              onClick={() => step(-1)}
              className={`${control} top-1/2 left-2 -translate-y-1/2 text-3xl`}
            >
              ‹
            </button>
            <button
              type="button"
              aria-label="Next image"
              onClick={() => step(1)}
              className={`${control} top-1/2 right-2 -translate-y-1/2 text-3xl`}
            >
              ›
            </button>
            <p className="absolute bottom-3 left-1/2 -translate-x-1/2 text-meta-sm text-on-overlay/70 tabular-nums">
              {index !== null && `${index + 1} / ${count}`}
            </p>
          </>
        )}
      </div>
    </dialog>
  );
}
