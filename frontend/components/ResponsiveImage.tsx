import type { ImageProps } from '../types';

type Props = { image: ImageProps; alt: string; sizes: string; eager?: boolean };

export default function ResponsiveImage({ image, alt, sizes, eager }: Props) {
  return (
    <img
      src={image.src}
      srcSet={image.srcset}
      sizes={sizes}
      width={image.width}
      height={image.height}
      alt={alt}
      loading={eager ? 'eager' : 'lazy'}
      decoding="async"
    />
  );
}
