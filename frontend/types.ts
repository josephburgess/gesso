export type Photo = { image: ImageProps; alt: string; caption: string };

export type About = { statement: string; biography: string[]; photos: Photo[] };

export type ArtworkTile = {
  title: string;
  year: number;
  href: string;
  cover: ImageProps | null;
  status: string;
  available: boolean;
  medium: string;
  size: string;
  price: string | null;
};

export type ArtworkDetail = {
  title: string;
  year: number;
  medium: string;
  size: string;
  images: ImageProps[];
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
  thumb: string;
};

export type Home = {
  intro: string;
  statement: string;
  about_href: string;
  featured: ArtworkTile[];
  index: ArtworkTile[];
  process: ProcessPhoto[];
};

export type ProcessPhoto = { image: ImageProps; caption: string; title: string };

export type Neighbour = { title: string; href: string };
export type NavLink = { label: string; href: string; current: boolean };

export type Appearance = {
  layout: 'rail' | 'top';
  work_layout: 'grid' | 'salon' | 'stack';
  headings: 'serif' | 'sans';
  motion: boolean;
  show_index: boolean;
  about_layout: 'beside' | 'above';
};

export type Site = { name: string; tagline: string; home_href: string; nav: NavLink[]; appearance: Appearance };

export type FlashMessage = { message: string };

declare module '@inertiajs/core' {
  export interface InertiaConfig {
    sharedPageProps: { site: Site };
    flashDataType: { messages?: FlashMessage[] };
  }
}
