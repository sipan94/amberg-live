/** Opening things outside the app: web pages, phone, e-mail, maps, calendar file, share sheet. */
import * as WebBrowser from "expo-web-browser";
import { Linking, Platform, Share } from "react-native";

/** Web pages open in an in-app browser (Safari View Controller / Chrome Custom Tab). */
export function openWeb(url: string) {
  return WebBrowser.openBrowserAsync(url).catch(() => Linking.openURL(url));
}

export function call(phone: string) {
  return Linking.openURL(`tel:${phone.replace(/[^\d+]/g, "")}`);
}

export function mail(address: string) {
  return Linking.openURL(`mailto:${address}`);
}

/** Opens Apple Maps / Google Maps with a route to the place. */
export function route({ lat, lng, address, label }: { lat?: number | null; lng?: number | null; address?: string | null; label: string }) {
  const query = lat != null && lng != null ? `${lat},${lng}` : encodeURIComponent(address || label);
  const url = Platform.select({
    ios: `https://maps.apple.com/?daddr=${query}&q=${encodeURIComponent(label)}`,
    default: `https://www.google.com/maps/dir/?api=1&destination=${query}`,
  });
  return Linking.openURL(url);
}

/**
 * Adds an event to the phone calendar via the website's .ics file (same as the web button).
 * iOS shows "Add to Calendar" in the in-app browser; Android hands the file to the calendar app.
 */
export function addToCalendar(icsUrl: string) {
  return Platform.OS === "ios" ? WebBrowser.openBrowserAsync(icsUrl) : Linking.openURL(icsUrl);
}

export function share(text: string, url: string) {
  return Share.share(Platform.OS === "ios" ? { message: text.replace(` – ${url}`, ""), url } : { message: text });
}
