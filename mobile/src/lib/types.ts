/** Shapes of the API answers (app/api/serializers.py in the main project). */

export type ImageRef = { url: string; small: string } | null;

export type Category = { id: number; name: string; slug: string; icon: string; color: string };

export type OrgBrief = {
  id: number;
  slug: string;
  name: string;
  type: "business" | "club";
  is_premium: boolean;
  logo: ImageRef;
};

export type Occurrence = {
  id: number;
  slug: string;
  title: string;
  start: string;
  end: string | null;
  when: string;
  ongoing: boolean;
  category: Category | null;
  location_name: string;
  lat: number | null;
  lng: number | null;
  is_free: boolean;
  price: string;
  is_featured: boolean;
  is_premium: boolean;
  is_highlight: boolean;
  recurrence: string;
  image: ImageRef;
  organization: OrgBrief;
};

export type Offer = {
  id: number;
  slug: string;
  title: string;
  description_html: string;
  description_text: string;
  valid_from: string;
  valid_until: string | null;
  validity: string;
  is_expired: boolean;
  is_featured: boolean;
  image: ImageRef;
  organization: OrgBrief;
  web_url: string;
};

export type HomeData = {
  today_label: string;
  today: Occurrence[];
  weekend_title: string;
  weekend: Occurrence[];
  upcoming: Occurrence[];
  offers: Offer[];
};

export type Meta = {
  site_name: string;
  categories: Category[];
  periods: { value: string; label: string }[];
  prices: { value: string; label: string }[];
  legal: Record<"impressum" | "datenschutz" | "agb" | "kontakt", string>;
  web_url: string;
};

export type Moderation = { status: string; status_label: string; rejection_reason: string | null };

export type User = {
  id: number;
  email: string;
  role: string;
  is_admin: boolean;
  is_verified: boolean;
  organization: (OrgBrief & Moderation) | null;
  pending?: number;
};
