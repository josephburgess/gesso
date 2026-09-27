export type Photo = { image: ImageProps; caption: string };

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
  framing: string;
  images: ImageProps[];
  status: string;
  available: boolean;
  price: string | null;
  description: string[];
};

export type Contact = {
  details: string;
  action: string;
  artwork: { title: string; slug: string } | null;
  topics: { value: string; label: string }[];
  topic: string;
};

export type Purchase = {
  enquire_href: string;
  enquire_label: string;
  action: string | null;
  note: string;
  notify: boolean;
};

export type ImageProps = {
  src: string;
  srcset: string;
  width: number;
  height: number;
  thumb: string;
  alt: string;
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
  theme: 'paper' | 'gallery' | 'slate';
  layout: 'rail' | 'top';
  work_layout: 'grid' | 'salon' | 'stack';
  headings: 'serif' | 'sans';
  motion: boolean;
  show_index: boolean;
  about_layout: 'beside' | 'above';
};

export type SocialLink = { label: string; href: string };

export type PageLink = { label: string; href: string };

export type Page = { title: string; blocks: { heading: boolean; text: string }[] };

export type Site = {
  name: string;
  tagline: string;
  home_href: string;
  nav: NavLink[];
  appearance: Appearance;
  social: SocialLink[];
  pages: PageLink[];
  privacy_href: string | null;
  subscribe_href: string;
};

export type FlashMessage = { message: string };

declare module '@inertiajs/core' {
  export interface InertiaConfig {
    sharedPageProps: { site: Site };
    flashDataType: { messages?: FlashMessage[] };
  }
}
