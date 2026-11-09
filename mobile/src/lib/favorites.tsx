/**
 * Merkliste: saved events, stored only on this phone (like localStorage on the website).
 * Optional reminders are local notifications scheduled by the phone – no server, no push token.
 */
import * as Notifications from "expo-notifications";
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Alert, Platform } from "react-native";

import { t } from "@/i18n/de";
import { load, save } from "./storage";

const KEY = "favorites.v1";
const REMINDER_KEY = "favorites.reminders";
const REMIND_BEFORE_MS = 2 * 60 * 60 * 1000;

export type Favorite = { slug: string; title: string; start: string; when: string; notificationId?: string };

type FavoritesState = {
  items: Favorite[];
  isFavorite: (slug: string) => boolean;
  toggle: (fav: Omit<Favorite, "notificationId">) => Promise<void>;
  remindersOn: boolean;
  setRemindersOn: (on: boolean) => Promise<void>;
};

const FavoritesContext = createContext<FavoritesState | null>(null);
const canNotify = Platform.OS !== "web";

if (canNotify) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: false,
      shouldSetBadge: false,
    }),
  });
}

async function askPermission(): Promise<boolean> {
  if (!canNotify) return false;
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("reminders", {
      name: t.favorites.remindersOn,
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }
  const current = await Notifications.getPermissionsAsync();
  if (current.granted) return true;
  const asked = await Notifications.requestPermissionsAsync({ ios: { allowAlert: true, allowSound: true } });
  return asked.granted;
}

async function schedule(fav: Favorite): Promise<string | undefined> {
  const at = new Date(fav.start).getTime() - REMIND_BEFORE_MS;
  if (!canNotify || Number.isNaN(at) || at <= Date.now()) return undefined;
  try {
    return await Notifications.scheduleNotificationAsync({
      content: {
        title: t.favorites.reminderTitle,
        body: t.favorites.reminderBody(fav.title, fav.when),
        data: { url: `/events/${fav.slug}` },
      },
      trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: new Date(at), channelId: "reminders" },
    });
  } catch {
    return undefined;
  }
}

async function cancel(fav: Favorite) {
  if (canNotify && fav.notificationId) {
    await Notifications.cancelScheduledNotificationAsync(fav.notificationId).catch(() => undefined);
  }
}

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Favorite[]>([]);
  const [remindersOn, setReminders] = useState(false);
  const itemsRef = useRef(items);
  itemsRef.current = items;

  useEffect(() => {
    (async () => {
      setItems(await load<Favorite[]>(KEY, []));
      setReminders(await load<boolean>(REMINDER_KEY, false));
    })();
  }, []);

  const persist = useCallback((next: Favorite[]) => {
    setItems(next);
    void save(KEY, next);
  }, []);

  const toggle = useCallback(async (fav: Omit<Favorite, "notificationId">) => {
    const existing = itemsRef.current.find((f) => f.slug === fav.slug);
    if (existing) {
      await cancel(existing);
      persist(itemsRef.current.filter((f) => f.slug !== fav.slug));
      return;
    }
    const entry: Favorite = { ...fav };
    if (remindersOn) entry.notificationId = await schedule(entry);
    persist([...itemsRef.current, entry]);
  }, [persist, remindersOn]);

  const setRemindersOn = useCallback(async (on: boolean) => {
    if (on && !(await askPermission())) {
      Alert.alert(t.favorites.remindersOn, t.errors.notifications);
      return;
    }
    setReminders(on);
    void save(REMINDER_KEY, on);
    // Re-plan reminders for everything already saved.
    const next: Favorite[] = [];
    for (const fav of itemsRef.current) {
      await cancel(fav);
      next.push({ ...fav, notificationId: on ? await schedule(fav) : undefined });
    }
    persist(next);
  }, [persist]);

  const value = useMemo<FavoritesState>(() => ({
    items,
    isFavorite: (slug) => items.some((f) => f.slug === slug),
    toggle,
    remindersOn,
    setRemindersOn,
  }), [items, toggle, remindersOn, setRemindersOn]);

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

export function useFavorites(): FavoritesState {
  const ctx = useContext(FavoritesContext);
  if (!ctx) throw new Error("useFavorites outside FavoritesProvider");
  return ctx;
}
