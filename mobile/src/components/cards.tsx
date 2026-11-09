/** Event and offer cards – same content and badges as the website's cards. */
import { Image } from "expo-image";
import { View } from "react-native";

import { t } from "@/i18n/de";
import type { Category, ImageRef, Occurrence, Offer } from "@/lib/types";
import { font, radius, space, tint, useTheme } from "@/theme";
import { AppText, Badge, Card, categoryIcon, Icon } from "./ui";

/** Photo, or a soft cover in the category colour for entries without one (like `.cover` on the web). */
export function Cover({ image, category, height }: { image: ImageRef; category?: Category | null; height: number }) {
  const theme = useTheme();
  if (image) {
    return (
      <Image
        source={{ uri: image.small }}
        style={{ width: "100%", height }}
        contentFit="cover"
        transition={150}
        accessibilityIgnoresInvertColors
      />
    );
  }
  const color = category?.color || "#736d63";
  return (
    <View style={{ height, alignItems: "center", justifyContent: "center", backgroundColor: tint(color, theme.dark ? 0.16 : 0.09, theme.dark ? "#24211d" : "#fbfaf8") }}>
      <Icon name={categoryIcon(category?.icon)} size={Math.round(height / 3.2)} color={color} />
    </View>
  );
}

/** Wide card for horizontal rows on the start screen. */
export function EventCard({ item, onPress, width }: { item: Occurrence; onPress: () => void; width?: number }) {
  return (
    <Card highlight={item.is_highlight} onPress={onPress} style={width ? { width } : undefined}>
      <Cover image={item.image} category={item.category} height={width ? Math.round(width * 0.5) : 150} />
      <View style={{ padding: space.md, gap: 4 }}>
        <Badges item={item} />
        <AppText variant="label" muted>{item.when}</AppText>
        <AppText variant="heading" numberOfLines={2} style={{ fontSize: 17, lineHeight: 22 }}>{item.title}</AppText>
        <AppText variant="small" muted numberOfLines={1}>{item.location_name}</AppText>
      </View>
    </Card>
  );
}

/** Compact row for lists (thumbnail left). */
export function EventRow({ item, onPress }: { item: Occurrence; onPress: () => void }) {
  return (
    <Card highlight={item.is_highlight} onPress={onPress} style={{ marginHorizontal: space.lg }}>
      <View style={{ flexDirection: "row" }}>
        <View style={{ width: 96, borderRadius: radius.md, overflow: "hidden" }}>
          <Cover image={item.image} category={item.category} height={104} />
        </View>
        <View style={{ flex: 1, padding: space.md, gap: 3, justifyContent: "center" }}>
          <Badges item={item} />
          <AppText variant="label" muted>{item.when}</AppText>
          <AppText variant="body" numberOfLines={2} style={{ fontFamily: font.semibold }}>{item.title}</AppText>
          <AppText variant="small" muted numberOfLines={1}>{item.location_name} · {item.price}</AppText>
        </View>
      </View>
    </Card>
  );
}

function Badges({ item }: { item: Occurrence }) {
  const badges = [
    item.ongoing && <Badge key="now" kind="now">{t.badges.now}</Badge>,
    item.is_featured && <Badge key="tip" kind="tip">{t.badges.tip}</Badge>,
    item.is_premium && <Badge key="premium" kind="premium">{t.badges.premium}</Badge>,
    item.is_free && <Badge key="free" kind="neutral">{t.badges.free}</Badge>,
  ].filter(Boolean);
  if (!badges.length) return null;
  return <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 2 }}>{badges}</View>;
}

export function OfferCard({ item, onPress, width }: { item: Offer; onPress: () => void; width?: number }) {
  return (
    <Card highlight={item.is_featured} onPress={onPress} style={width ? { width } : undefined}>
      <Cover image={item.image ?? item.organization.logo} height={width ? Math.round(width * 0.5) : 140} />
      <View style={{ padding: space.md, gap: 4 }}>
        <AppText variant="label" muted numberOfLines={1}>{item.organization.name}</AppText>
        <AppText variant="heading" numberOfLines={2} style={{ fontSize: 17, lineHeight: 22 }}>{item.title}</AppText>
        <AppText variant="small" muted numberOfLines={1}>{item.validity}</AppText>
      </View>
    </Card>
  );
}
