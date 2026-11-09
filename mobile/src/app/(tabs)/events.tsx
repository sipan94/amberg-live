/** Termine: list, calendar and map – one set of filters for all three (like the website). */
import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { FlatList, Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { EventCard, EventRow } from "@/components/cards";
import { Chip, ChipRow, SearchField, Segmented } from "@/components/controls";
import { EventMap } from "@/components/EventMap";
import { AppText, ErrorState, Icon, Loading } from "@/components/ui";
import { t } from "@/i18n/de";
import { api } from "@/lib/api";
import type { CalendarData, EventsPage, MapData, Meta, Occurrence } from "@/lib/types";
import { font, radius, space, useTheme } from "@/theme";

type View3 = "list" | "calendar" | "map";
type Filters = { zeitraum: string; kategorie: string; preis: string; q: string };

const openEvent = (slug: string) => router.push({ pathname: "/events/[slug]", params: { slug } });

export default function EventsScreen() {
  const insets = useSafeAreaInsets();
  const [view, setView] = useState<View3>("list");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters>({ zeitraum: "alle", kategorie: "", preis: "", q: "" });
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/meta"), staleTime: 60 * 60_000 });

  // Search waits until typing pauses, so the server isn't asked on every letter.
  useEffect(() => {
    const id = setTimeout(() => setFilters((f) => (f.q === search.trim() ? f : { ...f, q: search.trim() })), 350);
    return () => clearTimeout(id);
  }, [search]);

  const set = (patch: Partial<Filters>) => setFilters((f) => ({ ...f, ...patch }));
  const active = filters.zeitraum !== "alle" || filters.kategorie || filters.preis || filters.q;

  return (
    <View style={{ flex: 1, paddingTop: insets.top + space.md }}>
      <AppText variant="title" accessibilityRole="header" style={{ paddingHorizontal: space.lg, marginBottom: space.md }}>
        {t.events.title}
      </AppText>
      <Segmented<View3>
        value={view}
        onChange={setView}
        options={[{ value: "list", label: t.events.list }, { value: "calendar", label: t.events.calendar }, { value: "map", label: t.events.map }]}
      />
      <View style={{ gap: space.sm, paddingVertical: space.md }}>
        <SearchField value={search} onChangeText={setSearch} placeholder={t.events.search} />
        {view !== "calendar" ? (
          <ChipRow>
            {(meta.data?.periods ?? []).map((p) => (
              <Chip key={p.value} label={p.label} active={filters.zeitraum === p.value} onPress={() => set({ zeitraum: p.value })} />
            ))}
          </ChipRow>
        ) : null}
        <ChipRow>
          <Chip label={t.events.allCategories} active={!filters.kategorie} onPress={() => set({ kategorie: "" })} />
          {(meta.data?.categories ?? []).map((c) => (
            <Chip key={c.slug} label={c.name} active={filters.kategorie === c.slug} onPress={() => set({ kategorie: filters.kategorie === c.slug ? "" : c.slug })} />
          ))}
          {(meta.data?.prices ?? []).filter((p) => p.value).map((p) => (
            <Chip key={p.value} label={p.label} active={filters.preis === p.value} onPress={() => set({ preis: filters.preis === p.value ? "" : p.value })} />
          ))}
          {active ? (
            <Chip label={t.events.reset} onPress={() => { setSearch(""); setFilters({ zeitraum: "alle", kategorie: "", preis: "", q: "" }); }} />
          ) : null}
        </ChipRow>
      </View>
      {view === "list" ? <EventList filters={filters} /> : view === "calendar" ? <MonthCalendar filters={filters} /> : <MapView filters={filters} />}
    </View>
  );
}

// ---- list -----------------------------------------------------------------------------------

type Row = { type: "tips"; items: Occurrence[] } | { type: "day"; key: string; label: string } | { type: "event"; key: string; item: Occurrence };

function EventList({ filters }: { filters: Filters }) {
  const q = useInfiniteQuery({
    queryKey: ["events", filters],
    queryFn: ({ pageParam, signal }) => api<EventsPage>("/events", { params: { ...filters, seite: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.has_next ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
  });

  const rows = useMemo<Row[]>(() => {
    if (!q.data) return [];
    const out: Row[] = [];
    const tips = q.data.pages[0]?.tips ?? [];
    if (tips.length) out.push({ type: "tips", items: tips });
    let lastDay = "";
    for (const page of q.data.pages) {
      for (const day of page.days) {
        if (day.date !== lastDay) {
          out.push({ type: "day", key: `d-${day.date}`, label: day.label });
          lastDay = day.date;
        }
        for (const item of day.items) out.push({ type: "event", key: `${item.id}-${item.start}`, item });
      }
    }
    return out;
  }, [q.data]);

  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const total = q.data.pages[0]?.total ?? 0;

  return (
    <FlatList
      data={rows}
      keyExtractor={(r) => (r.type === "tips" ? "tips" : r.key)}
      contentContainerStyle={{ paddingBottom: space.xxl, gap: space.sm }}
      onEndReached={() => q.hasNextPage && !q.isFetchingNextPage && q.fetchNextPage()}
      onEndReachedThreshold={0.6}
      refreshControl={<RefreshControl refreshing={q.isRefetching && !q.isFetchingNextPage} onRefresh={() => void q.refetch()} />}
      ListHeaderComponent={<AppText variant="small" muted style={{ paddingHorizontal: space.lg }}>{t.events.results(total)}</AppText>}
      ListEmptyComponent={<AppText muted style={{ padding: space.lg }}>{t.events.noResults}</AppText>}
      ListFooterComponent={q.isFetchingNextPage ? <Loading /> : undefined}
      renderItem={({ item: r }) => {
        if (r.type === "tips") {
          return (
            <View style={{ gap: space.sm, marginBottom: space.sm }}>
              <AppText variant="heading" style={{ paddingHorizontal: space.lg, marginTop: space.sm }}>{t.events.topTips}</AppText>
              <FlatList
                horizontal
                data={r.items}
                keyExtractor={(e) => `tip-${e.id}`}
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ paddingHorizontal: space.lg, gap: space.md }}
                renderItem={({ item: e }) => <EventCard item={e} width={260} onPress={() => openEvent(e.slug)} />}
              />
            </View>
          );
        }
        if (r.type === "day") {
          return <AppText variant="heading" style={{ paddingHorizontal: space.lg, marginTop: space.md, fontSize: 16 }}>{r.label}</AppText>;
        }
        return <EventRow item={r.item} onPress={() => openEvent(r.item.slug)} />;
      }}
    />
  );
}

// ---- calendar -------------------------------------------------------------------------------

function MonthCalendar({ filters }: { filters: Filters }) {
  const theme = useTheme();
  const [month, setMonth] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const q = useQuery({
    queryKey: ["calendar", month, filters.kategorie, filters.preis, filters.q],
    queryFn: ({ signal }) => api<CalendarData>("/events/calendar", {
      params: { monat: month, kategorie: filters.kategorie, preis: filters.preis, q: filters.q }, signal,
    }),
    placeholderData: keepPreviousData,
  });

  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  const c = q.data;
  const day = selected && selected.startsWith(c.month) ? selected : c.today.startsWith(c.month) ? c.today : null;
  const cells: (string | null)[] = [
    ...Array<null>(c.first_weekday).fill(null),
    ...Array.from({ length: c.days_in_month }, (_, i) => `${c.month}-${String(i + 1).padStart(2, "0")}`),
  ];
  const dayItems = day ? c.days[day] ?? [] : [];

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: space.xxl }}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: space.lg, marginBottom: space.sm }}>
        <NavButton icon="chevron-left" label={c.prev} onPress={() => { setMonth(c.prev); setSelected(null); }} />
        <AppText variant="heading">{c.title}</AppText>
        <NavButton icon="chevron-right" label={c.next} onPress={() => { setMonth(c.next); setSelected(null); }} />
      </View>
      <View style={{ flexDirection: "row", paddingHorizontal: space.md }}>
        {c.weekdays.map((w) => (
          <Text key={w} style={{ flex: 1, textAlign: "center", fontFamily: font.medium, fontSize: 12, color: theme.textMuted, paddingVertical: 4 }}>{w}</Text>
        ))}
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", paddingHorizontal: space.md }}>
        {cells.map((d, i) => {
          if (!d) return <View key={`e${i}`} style={{ width: `${100 / 7}%`, aspectRatio: 1 }} />;
          const count = c.days[d]?.length ?? 0;
          const isSel = d === day;
          const isToday = d === c.today;
          const past = d < c.today;
          return (
            <Pressable
              key={d}
              onPress={() => setSelected(d)}
              accessibilityRole="button"
              accessibilityLabel={`${Number(d.slice(8))}. – ${t.events.results(count)}`}
              accessibilityState={{ selected: isSel }}
              style={{ width: `${100 / 7}%`, aspectRatio: 1, padding: 3 }}
            >
              <View style={{
                flex: 1, borderRadius: radius.md, alignItems: "center", justifyContent: "center", gap: 3,
                backgroundColor: isSel ? theme.accent : count ? theme.card : "transparent",
                borderWidth: isToday && !isSel ? 1.5 : count && !isSel ? 1 : 0,
                borderColor: isToday ? theme.accent : theme.cardBorder,
              }}>
                <Text style={{ fontFamily: count ? font.semibold : font.regular, fontSize: 15, color: isSel ? "#1a1815" : past ? theme.textMuted : theme.text }}>
                  {Number(d.slice(8))}
                </Text>
                {count ? <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: isSel ? "#1a1815" : theme.accentText }} /> : null}
              </View>
            </Pressable>
          );
        })}
      </View>
      <View style={{ gap: space.sm, marginTop: space.lg }}>
        {day ? (
          dayItems.length ? (
            dayItems.map((e) => <EventRow key={`${e.id}-${e.start}`} item={e} onPress={() => openEvent(e.slug)} />)
          ) : (
            <AppText muted style={{ paddingHorizontal: space.lg }}>{t.events.noEventsDay}</AppText>
          )
        ) : null}
      </View>
    </ScrollView>
  );
}

function NavButton({ icon, label, onPress }: { icon: "chevron-left" | "chevron-right"; label: string; onPress: () => void }) {
  const theme = useTheme();
  return (
    <Pressable onPress={onPress} hitSlop={10} accessibilityRole="button" accessibilityLabel={label}
      style={{ width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: theme.card, borderWidth: 1, borderColor: theme.cardBorder }}>
      <Icon name={icon} size={20} />
    </Pressable>
  );
}

// ---- map --------------------------------------------------------------------------------------

function MapView({ filters }: { filters: Filters }) {
  const q = useQuery({
    queryKey: ["map", filters],
    queryFn: ({ signal }) => api<MapData>("/events/map", { params: filters, signal }),
    placeholderData: keepPreviousData,
  });
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorState message={q.error.message} onRetry={() => q.refetch()} />;
  return (
    <View style={{ flex: 1, paddingHorizontal: space.lg, paddingBottom: space.lg, gap: space.sm }}>
      {q.data.missing ? <AppText variant="small" muted>{t.events.mapMissing(q.data.missing)}</AppText> : null}
      <EventMap markers={q.data.markers} center={q.data.center} tilesUrl={q.data.tiles.url} onOpen={openEvent} />
    </View>
  );
}
