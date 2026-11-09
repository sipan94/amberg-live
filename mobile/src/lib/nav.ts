/** Go back if there is a screen to go back to, otherwise open a sensible screen. */
import { Href, router } from "expo-router";

export function goBack(fallback: Href) {
  if (router.canGoBack()) router.back();
  else router.replace(fallback);
}
