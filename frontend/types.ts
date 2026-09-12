export type ArtworkTile = { title: string; year: number; href: string; cover: ImageProps | null };

export type ArtworkDetail = {
  title: string;
  year: number;
  medium: string;
  size: string;
  cover: ImageProps | null;
};

export type ImageProps = {
  src: string;
  srcset: string;
  width: number;
  height: number;
};

export type NavLink = { label: string; href: string; current: boolean };

export type Site = { name: string; tagline: string; home_href: string; nav: NavLink[] };

declare module '@inertiajs/core' {
  export interface InertiaConfig {
    sharedPageProps: { site: Site };
  }
}
