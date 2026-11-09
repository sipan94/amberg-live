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

export type PageMeta = { page: number; pages: number; total: number; has_next: boolean; has_prev: boolean };

export type EventsPage = PageMeta & {
  tips: Occurrence[];
  days: { date: string; label: string; items: Occurrence[] }[];
  filter: { period: string; category: string | null; price: string | null; q: string; von: string | null; bis: string | null };
};

export type CalendarData = {
  month: string;
  title: string;
  prev: string;
  next: string;
  weekdays: string[];
  first_weekday: number; // 0 = Monday
  days_in_month: number;
  today: string;
  days: Record<string, Occurrence[]>;
};

export type MapData = {
  markers: Occurrence[];
  missing: number;
  tiles: { url: string; attribution: string };
  center: { lat: number; lng: number };
};

export type EventDetail = {
  id: number;
  slug: string;
  title: string;
  description_html: string;
  description_text: string;
  start: string;
  end: string | null;
  when: string;
  recurrence: string;
  recurrence_label: string | null;
  recurrence_until: string | null;
  next_dates: { start: string; end: string | null; when: string }[];
  is_past: boolean;
  location_name: string;
  address: string | null;
  lat: number | null;
  lng: number | null;
  is_free: boolean;
  price: string;
  category: Category | null;
  is_featured: boolean;
  image: ImageRef;
  organization: OrgBrief;
  web_url: string;
  ics_url: string;
  share_text: string;
  more_from_organizer: Occurrence[];
};

export type Paged<T> = PageMeta & { items: T[] };

export type OrgListItem = OrgBrief & { summary: string; type_label: string };

export type Organization = OrgBrief & {
  description_html: string;
  description_text: string;
  address: string | null;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  opening_hours: { day: string; label: string; value: string }[];
  cover_image: ImageRef;
  web_url: string;
  events: Occurrence[];
  offers: Offer[];
};

export type MyEvent = Moderation & {
  id: number; slug: string; title: string; start: string; end: string | null; when: string;
  recurrence: string; recurrence_until: string | null; category_id: number; location_name: string; address: string | null;
  is_free: boolean; price_info: string | null; description_text: string; image: ImageRef; is_featured: boolean; view_count: number;
};

export type MyOffer = Moderation & {
  id: number; slug: string; title: string; valid_from: string; valid_until: string | null;
  description_text: string; image: ImageRef; view_count: number;
};

export type MyOrganization = Organization & Moderation & { opening_hours_raw: Record<string, string> };

export type Overview = { user: User; organization: Omit<MyOrganization, "events" | "offers"> | null; events: MyEvent[]; offers: MyOffer[] };

export type FormOptions = {
  categories: { id: number; name: string }[];
  recurrence: { value: string; label: string }[];
  org_types: { value: "business" | "club"; label: string }[];
  weekdays: { key: string; label: string }[];
  rights_label: string;
  review_note: string;
};

export type SaveResult<T> = { message: string; pending: boolean; item: T };
