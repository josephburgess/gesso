import { useEffect, useRef, useState } from 'react';
import type { ImageProps } from '@/types';

type Props = {
  image: ImageProps;
  alt: string;
  sizes: string;
  eager?: boolean;
  reveal?: boolean;
  className?: string;
};

export default function ResponsiveImage({ image, alt, sizes, eager, reveal, className = '' }: Props) {
  const ref = useRef<HTMLImageElement>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (element?.complete && element.naturalWidth) setLoaded(true);
  }, [image.src]);

  const revealClass = reveal ? `transition-image-reveal ${loaded ? '' : 'scale-[1.015] opacity-0'}` : '';

  return (
    <img
      ref={ref}
      src={image.src}
      srcSet={image.srcset}
      sizes={sizes}
      width={image.width}
      height={image.height}
      alt={alt}
      loading={eager ? 'eager' : 'lazy'}
      fetchPriority={eager ? 'high' : undefined}
      onLoad={() => setLoaded(true)}
      className={`${revealClass} ${className}`}
      decoding="async"
    />
  );
}
