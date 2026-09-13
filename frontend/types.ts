export type About = { statement: string; biography: string[] };

export type ArtworkTile = {
  title: string;
  year: number;
  href: string;
  cover: ImageProps | null;
  status: string;
  available: boolean;
};

export type ArtworkDetail = {
  title: string;
  year: number;
  medium: string;
  size: string;
  cover: ImageProps | null;
  status: string;
  available: boolean;
  price: string | null;
  description: string[];
};

export type Contact = { details: string };

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
