import ResponsiveImage from '@/components/ResponsiveImage';
import type { ImageProps } from '@/types';

type Props = { image: ImageProps; alt?: string; caption?: string; sizes: string; eager?: boolean };

export default function Figure({ image, alt, caption, sizes, eager }: Props) {
  return (
    <figure>
      <ResponsiveImage image={image} alt={alt} sizes={sizes} eager={eager} reveal className="w-full" />
      {caption && <figcaption className="pt-2.5 text-meta-sm text-ink-dim">{caption}</figcaption>}
    </figure>
  );
}
