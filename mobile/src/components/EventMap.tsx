/**
 * Event map: Leaflet inside a WebView – the same map library as the website.
 * Privacy like the website: OpenStreetMap tiles load only after the user agrees (two-click),
 * optionally remembered on this phone. Leaflet itself comes from our own server.
 */
import { createElement, useEffect, useMemo, useState } from "react";
import { Platform, Switch, View } from "react-native";
import { WebView, WebViewMessageEvent } from "react-native-webview";

import { t } from "@/i18n/de";
import { API_ROOT } from "@/lib/api";
import { load, save } from "@/lib/storage";
import type { Occurrence } from "@/lib/types";
import { radius, space, useTheme } from "@/theme";
import { AppText, Button, Card, Icon } from "./ui";

const CONSENT_KEY = "map.consent";

type Props = {
  markers: Pick<Occurrence, "slug" | "title" | "when" | "lat" | "lng" | "category">[];
  center: { lat: number; lng: number };
  tilesUrl: string;
  zoom?: number;
  onOpen?: (slug: string) => void;
  height?: number;
};

export function EventMap({ markers, center, tilesUrl, zoom = 14, onOpen, height }: Props) {
  const theme = useTheme();
  const [consent, setConsent] = useState<boolean | null>(null);
  const [remember, setRemember] = useState(false);

  useEffect(() => {
    load<boolean>(CONSENT_KEY, false).then(setConsent);
  }, []);

  const html = useMemo(() => buildHtml(markers, center, tilesUrl, zoom, theme.dark, !!onOpen), [markers, center, tilesUrl, zoom, theme.dark, onOpen]);

  useEffect(() => {
    if (Platform.OS !== "web" || !onOpen) return;
    const listener = (e: MessageEvent) => typeof e.data === "string" && e.data.startsWith("open:") && onOpen(e.data.slice(5));
    window.addEventListener("message", listener);
    return () => window.removeEventListener("message", listener);
  }, [onOpen]);

  const box = { height, flex: height ? undefined : 1, borderRadius: radius.lg, overflow: "hidden" as const };

  if (consent === null) return <View style={box} />;

  if (!consent) {
    return (
      <Card style={{ minHeight: height, flex: height ? undefined : 1, justifyContent: "center", padding: space.xl, gap: space.md }}>
        <Icon name="map" size={26} />
        <AppText variant="heading">{t.map.consentTitle}</AppText>
        <AppText variant="small" muted>{t.map.consentText}</AppText>
        <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
          <Switch value={remember} onValueChange={setRemember} trackColor={{ true: theme.accent }} accessibilityLabel={t.map.consentRemember} />
          <AppText variant="small" style={{ flex: 1 }}>{t.map.consentRemember}</AppText>
        </View>
        <Button
          title={t.map.consentButton}
          onPress={() => {
            setConsent(true);
            if (remember) void save(CONSENT_KEY, true);
          }}
        />
      </Card>
    );
  }

  if (Platform.OS === "web") {
    // Expo web preview only: an iframe instead of the native WebView.
    return <View style={box}>{createElement("iframe", { srcDoc: html, style: { border: 0, width: "100%", height: "100%" }, title: t.events.map })}</View>;
  }

  return (
    <View style={box}>
      <WebView
        originWhitelist={["*"]}
        source={{ html, baseUrl: API_ROOT }}
        onMessage={(e: WebViewMessageEvent): void => {
          const msg: string = e.nativeEvent.data;
          if (msg.startsWith("open:")) onOpen?.(msg.slice(5));
        }}
        style={{ backgroundColor: theme.bg }}
        setSupportMultipleWindows={false}
      />
    </View>
  );
}

function buildHtml(markers: Props["markers"], center: Props["center"], tilesUrl: string, zoom: number, dark: boolean, canOpen: boolean): string {
  const points = markers
    .filter((m) => m.lat != null && m.lng != null)
    .map((m) => ({ slug: m.slug, title: m.title, when: m.when, lat: m.lat, lng: m.lng, color: m.category?.color || "#855815" }));
  // JSON inside <script>: escape "<" so a title can never close the script tag.
  const data = JSON.stringify({ points, center, tilesUrl, zoom, dark, canOpen }).replace(/</g, "\\u003c");
  return `<!doctype html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<link rel="stylesheet" href="${API_ROOT}/static/vendor/leaflet/leaflet.css">
<style>
  html,body,#map{margin:0;height:100%;background:${dark ? "#1a1815" : "#f6f5f2"};font-family:-apple-system,system-ui,sans-serif}
  .pop b{display:block;font-size:15px;margin-bottom:2px}.pop span{color:#736d63;font-size:13px}
  .pop button{margin-top:8px;width:100%;padding:8px;border:0;border-radius:8px;background:#e3a92b;color:#1a1815;font-weight:600;font-size:14px}
  ${dark ? ".leaflet-tile-pane{filter:brightness(.75) contrast(1.1) saturate(.8)}" : ""}
</style></head><body><div id="map"></div>
<script src="${API_ROOT}/static/vendor/leaflet/leaflet.js"></script>
<script>
  var d = ${data};
  function send(msg){ if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(msg); else parent.postMessage(msg, "*"); }
  var map = L.map("map", { zoomControl: false }).setView([d.center.lat, d.center.lng], d.zoom);
  L.tileLayer(d.tilesUrl, { maxZoom: 19, attribution: "${t.map.attribution}" }).addTo(map);
  var bounds = [];
  d.points.forEach(function (p) {
    var el = document.createElement("div"); el.className = "pop";
    var b = document.createElement("b"); b.textContent = p.title; el.appendChild(b);
    var s = document.createElement("span"); s.textContent = p.when; el.appendChild(s);
    if (d.canOpen) { var btn = document.createElement("button"); btn.textContent = "Ansehen";
    btn.onclick = function () { send("open:" + p.slug); }; el.appendChild(btn); }
    L.circleMarker([p.lat, p.lng], { radius: 9, color: "#fff", weight: 2, fillColor: p.color, fillOpacity: 0.95 })
      .addTo(map).bindPopup(el);
    bounds.push([p.lat, p.lng]);
  });
  if (bounds.length > 1) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
</script></body></html>`;
}
