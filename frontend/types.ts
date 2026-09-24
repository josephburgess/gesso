export type About = { statement: string; biography: string[] };

export type ArtworkTile = {
  title: string;
  year: number;
  href: string;
  cover: ImageProps | null;
  status: string;
  available: boolean;
  medium: string;
  size: string;
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

export type Contact = { details: string; action: string; artwork: { title: string; slug: string } | null };

export type Purchase = { enquire_href: string; enquire_label: string; action: string | null; note: string };

export type ImageProps = {
  src: string;
  srcset: string;
  width: number;
  height: number;
};

export type Home = {
  intro: string;
  statement: string;
  about_href: string;
  featured: ArtworkTile[];
  index: ArtworkTile[];
};
export type NavLink = { label: string; href: string; current: boolean };

export type Site = { name: string; tagline: string; home_href: string; nav: NavLink[] };

export type FlashMessage = { message: string };

declare module '@inertiajs/core' {
  export interface InertiaConfig {
    sharedPageProps: { site: Site };
    flashDataType: { messages?: FlashMessage[] };
  }
}
