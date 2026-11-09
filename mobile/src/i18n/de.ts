/**
 * All texts of the app in one place (German), like app/i18n/de.json on the website.
 * Content labels (dates, prices, error messages) come ready-made from the server.
 */
export const de = {
  appName: "Amberg Live",
  tabs: {
    home: "Start",
    events: "Termine",
    offers: "Angebote",
    places: "Orte",
    account: "Konto",
  },
  home: {
    greeting: "Was ist los in Amberg?",
    today: "Heute",
    nothingToday: "Heute steht nichts im Kalender.",
    upcoming: "Demnächst",
    offers: "Aktuelle Angebote",
    allEvents: "Alle Termine",
    allOffers: "Alle Angebote",
  },
  badges: {
    tip: "Tipp",
    premium: "Premium",
    free: "Kostenlos",
    now: "Läuft gerade",
  },
  common: {
    loading: "Lädt …",
    retry: "Nochmal versuchen",
    soon: "Kommt in der nächsten Version.",
  },
  errors: {
    offline: "Keine Verbindung zum Server. Bist du online?",
    generic: "Da ist etwas schiefgelaufen. Bitte versuche es nochmal.",
  },
} as const;

export const t = de;
