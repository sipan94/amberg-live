"""Realistic demo content for Amberg.

All businesses and clubs are FICTIONAL (contact data uses example.com and
placeholder phone numbers). Venues are real Amberg places; coordinates are
approximate. Dates are relative to the day you run `flask seed`, so the demo
always has something "heute", "am Wochenende" and "demnächst".
"""
from datetime import date, datetime, time, timedelta

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

# Real venues in Amberg (approximate coordinates).
VENUES = {
    "marktplatz": ("Marktplatz Amberg", "Marktplatz, 92224 Amberg", 49.4448, 11.8581),
    "acc": ("Amberger Congress Centrum (ACC)", "Schießstätteweg 8, 92224 Amberg", 49.4466, 11.8524),
    "theater": ("Stadttheater Amberg", "Schrannenplatz 8, 92224 Amberg", 49.4457, 11.8606),
    "luftmuseum": ("Luftmuseum Amberg", "Eichenforstgäßchen 12, 92224 Amberg", 49.4441, 11.8566),
    "stadtbrille": ("Stadtbrille am Vilsufer", "Schiffgasse, 92224 Amberg", 49.4432, 11.8549),
    "kurfuerstenbad": ("Kurfürstenbad", "Kurfürstenring 2, 92224 Amberg", 49.4413, 11.8641),
    "mariahilfberg": ("Mariahilfberg", "Mariahilfbergweg, 92224 Amberg", 49.4497, 11.8745),
}


def at(day: date, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return datetime.combine(day, time(hour, minute))


def next_weekday(today: date, weekday: int) -> date:
    """Today if it is that weekday, otherwise the next one."""
    return today + timedelta(days=(weekday - today.weekday()) % 7)


def last_weekday(today: date, weekday: int) -> date:
    """Today if it is that weekday, otherwise the previous one."""
    return today - timedelta(days=(today.weekday() - weekday) % 7)


def p(*paragraphs: str) -> str:
    return "".join(f"<p>{text}</p>" for text in paragraphs)


ORGANIZATIONS = [
    {
        "key": "redaktion", "owner": "ADMIN", "name": "Amberg Live Redaktion", "type": "business",
        "description": p("Die Redaktion von Amberg Live trägt öffentliche Termine der Stadt "
                         "zusammen – vom Wochenmarkt bis zum Christkindlmarkt."),
        "address": "Marktplatz, 92224 Amberg", "lat": 49.4448, "lng": 11.8581,
        "email": "redaktion@example.com", "website": None, "phone": None, "hours": None,
        "premium": False, "status": "approved",
    },
    {
        "key": "cafe", "owner": "cafe-vilsufer@example.com", "name": "Café am Vilsufer",
        "type": "business",
        "description": p("Gemütliches Café direkt an der Vils mit hausgemachten Kuchen, "
                         "Frühstück bis 14 Uhr und regelmäßiger Live-Musik.",
                         "Im Sommer mit Terrasse am Wasser."),
        "address": "Schiffgasse 5, 92224 Amberg", "lat": 49.4435, "lng": 11.8556,
        "email": "hallo@example.com", "website": "https://example.com/cafe-vilsufer",
        "phone": "09621 000 001",
        "hours": {"mo": "geschlossen", "di": "08:00–18:00", "mi": "08:00–18:00",
                  "do": "08:00–18:00", "fr": "08:00–22:00", "sa": "08:00–22:00",
                  "so": "09:00–18:00"},
        "premium": True, "status": "approved",
    },
    {
        "key": "buch", "owner": "seitenweise@example.com", "name": "Buchhandlung Seitenweise",
        "type": "business",
        "description": p("Unabhängige Buchhandlung in der Altstadt. Große Kinderbuch-Ecke, "
                         "Lesungen und Bestellservice bis zum nächsten Tag."),
        "address": "Georgenstraße 20, 92224 Amberg", "lat": 49.4452, "lng": 11.8562,
        "email": "laden@example.com", "website": "https://example.com/seitenweise",
        "phone": "09621 000 002",
        "hours": {"mo": "09:30–18:30", "di": "09:30–18:30", "mi": "09:30–18:30",
                  "do": "09:30–18:30", "fr": "09:30–18:30", "sa": "09:30–16:00",
                  "so": "geschlossen"},
        "premium": False, "status": "approved",
    },
    {
        "key": "gasthaus", "owner": "gasthaus-vils@example.com", "name": "Gasthaus Zur Vils",
        "type": "business",
        "description": p("Oberpfälzer Wirtshausküche mit Zutaten aus der Region: "
                         "Schäufele, Zoigl und Kartoffelknödel wie bei Oma."),
        "address": "Vilstorplatz 3, 92224 Amberg", "lat": 49.4426, "lng": 11.8580,
        "email": "tisch@example.com", "website": "https://example.com/gasthaus-vils",
        "phone": "09621 000 003",
        "hours": {"mo": "Ruhetag", "di": "11:00–22:00", "mi": "11:00–22:00",
                  "do": "11:00–22:00", "fr": "11:00–23:00", "sa": "11:00–23:00",
                  "so": "11:00–21:00"},
        "premium": False, "status": "approved",
    },
    {
        "key": "wein", "owner": "weinhandlung@example.com", "name": "Weinhandlung Kurfürst",
        "type": "business",
        "description": p("Weine aus Franken und der ganzen Welt, dazu Feinkost und "
                         "monatliche Weinproben im Gewölbekeller."),
        "address": "Rathausstraße 9, 92224 Amberg", "lat": 49.4446, "lng": 11.8592,
        "email": "wein@example.com", "website": "https://example.com/weinhandlung",
        "phone": "09621 000 004", "hours": None,
        "premium": False, "status": "approved",
    },
    {
        "key": "lauf", "owner": "laufgruppe@example.com", "name": "Laufgruppe Vilstal e.V.",
        "type": "club",
        "description": p("Wir laufen jeden Dienstag und Samstag gemeinsam – vom Einsteiger "
                         "bis zum Marathon. Neue Mitglieder sind immer willkommen!"),
        "address": "Kurfürstenring 2, 92224 Amberg", "lat": 49.4413, "lng": 11.8641,
        "email": "lauf@example.com", "website": "https://example.com/laufgruppe",
        "phone": None, "hours": None, "premium": False, "status": "approved",
    },
    {
        "key": "schach", "owner": "schach@example.com", "name": "Schachfreunde Amberg e.V.",
        "type": "club",
        "description": p("Spielabend jeden Freitag ab 19 Uhr. Jugendtraining, "
                         "Mannschaftsspiele und offene Turniere."),
        "address": "Paulanerplatz 1, 92224 Amberg", "lat": 49.4462, "lng": 11.8575,
        "email": "schach@example.com", "website": None, "phone": None, "hours": None,
        "premium": False, "status": "approved",
    },
    {
        "key": "tracht", "owner": "trachtenverein@example.com",
        "name": "Trachtenverein D'Vilstaler e.V.", "type": "club",
        "description": p("Volkstanz, Tracht und Brauchtum aus der Oberpfalz. "
                         "Probenabend jeden Donnerstag – Zuschauer gern gesehen."),
        "address": "Amberg", "lat": None, "lng": None,
        "email": "tracht@example.com", "website": None, "phone": None, "hours": None,
        "premium": False, "status": "approved",
    },
    {
        # Waiting for approval: shows up in the admin moderation queue.
        "key": "rad", "owner": "radundtat@example.com", "name": "Fahrradwerkstatt Rad & Tat",
        "type": "business",
        "description": p("Reparatur, Service und gebrauchte Räder. Schnellservice am selben Tag."),
        "address": "Bahnhofstraße 14, 92224 Amberg", "lat": 49.4418, "lng": 11.8618,
        "email": "werkstatt@example.com", "website": None, "phone": "09621 000 005",
        "hours": None, "premium": False, "status": "pending",
    },
]


def build_events(today: date) -> list[dict]:
    sat = next_weekday(today, SAT)
    sun = next_weekday(today, SUN)
    fri = next_weekday(today, FRI)
    v = VENUES

    return [
        dict(org="redaktion", cat="maerkte-feste", title="Wochenmarkt am Marktplatz",
             start=at(last_weekday(today, SAT) - timedelta(weeks=4), "07:00"), dur_h=5,
             venue=v["marktplatz"], recurrence="weekly",
             desc=p("Obst, Gemüse, Käse, Brot und Blumen von Erzeugern aus der Region. "
                    "Jeden Samstagvormittag rund ums Rathaus.")),
        dict(org="cafe", cat="konzerte-party", title="Live-Jazz am Vilsufer",
             start=at(today, "19:30"), dur_h=2.5, featured=True,
             venue=("Café am Vilsufer", "Schiffgasse 5, 92224 Amberg", 49.4435, 11.8556),
             desc=p("Das Trio „Blue Vils“ spielt Jazz-Standards und Bossa Nova. "
                    "Eintritt frei – Hut geht rum.")),
        dict(org="cafe", cat="essen-trinken", title="Sonntagsbrunch",
             start=at(last_weekday(today, SUN) - timedelta(weeks=2), "10:00"), dur_h=3,
             recurrence="weekly", free=False, price="24,50 € p. P.",
             venue=("Café am Vilsufer", "Schiffgasse 5, 92224 Amberg", 49.4435, 11.8556),
             desc=p("Großes Brunch-Buffet mit regionalen Produkten. Bitte reservieren.")),
        dict(org="buch", cat="familie-kinder", title="Vorlesestunde für Kinder",
             start=at(last_weekday(today, WED) - timedelta(weeks=3), "15:00"), dur_h=1,
             recurrence="weekly",
             venue=("Buchhandlung Seitenweise", "Georgenstraße 20, 92224 Amberg", 49.4452, 11.8562),
             desc=p("Für Kinder von 4 bis 8 Jahren. Eltern dürfen gern dabeibleiben.")),
        dict(org="redaktion", cat="kultur-museen", title="Familienführung im Luftmuseum",
             start=at(sat, "14:00"), dur_h=1.5, free=False, price="5 €, Kinder frei",
             venue=v["luftmuseum"], featured=True,
             desc=p("Eine Stunde voller Luftkunst zum Anfassen – ideal für Familien.")),
        dict(org="redaktion", cat="kultur-museen", title="Altstadtführung: Stadtbrille & Stadtmauer",
             start=at(today - timedelta(days=40), "11:00"), dur_h=1.5, recurrence="monthly",
             free=False, price="8 €", venue=v["stadtbrille"],
             desc=p("Rundgang zu den Highlights der Amberger Altstadt mit "
                    "zertifizierter Gästeführung. Treffpunkt an der Stadtbrille.")),
        dict(org="wein", cat="essen-trinken", title="Weinprobe: Franken trifft Südtirol",
             start=at(sat, "18:00"), dur_h=3, free=False, price="39 €",
             venue=("Weinhandlung Kurfürst", "Rathausstraße 9, 92224 Amberg", 49.4446, 11.8592),
             desc=p("Acht Weine, dazu Brot und Käse. Begrenzte Plätze.")),
        dict(org="redaktion", cat="konzerte-party", title="Ü30-Party im ACC",
             start=at(fri, "21:00") if fri > today else at(fri + timedelta(weeks=1), "21:00"),
             dur_h=6, free=False, price="10 €", venue=v["acc"],
             desc=p("Hits der 80er, 90er und 2000er auf zwei Floors.")),
        dict(org="redaktion", cat="kultur-museen", title="Kabarett: „Oberpfalz für Anfänger“",
             start=at(today + timedelta(days=6), "20:00"), dur_h=2, free=False,
             price="VVK 22 €, AK 25 €", venue=v["theater"],
             desc=p("Ein Abend über Zoigl, Dialekt und die Frage, warum hier alles „basst“.")),
        dict(org="gasthaus", cat="essen-trinken", title="Kochkurs: Oberpfälzer Küche",
             start=at(today + timedelta(days=9), "17:00"), dur_h=4, free=False, price="45 €",
             venue=("Gasthaus Zur Vils", "Vilstorplatz 3, 92224 Amberg", 49.4426, 11.8580),
             desc=p("Gemeinsam kochen wir Schäufele mit Knödeln und Blaukraut.")),
        dict(org="redaktion", cat="familie-kinder", title="Familientag im Kurfürstenbad",
             start=at(sun + timedelta(weeks=1), "10:00"), dur_h=7, free=False,
             price="Familienkarte 15 €", venue=v["kurfuerstenbad"],
             desc=p("Wasserrutschen-Rallye, Schwimmabzeichen-Schnupperkurs und Spiele.")),
        dict(org="lauf", cat="sport", title="Vilstal-Lauf 10 km",
             start=at(today + timedelta(days=13), "10:00"), dur_h=3, free=False,
             price="12 € Startgebühr", venue=v["kurfuerstenbad"],
             desc=p("Flache, schnelle Strecke entlang der Vils. Auch 5 km und Kinderlauf.")),
        dict(org="schach", cat="vereine", title="Offenes Schnellschach-Turnier",
             start=at(today + timedelta(days=20), "13:00"), dur_h=6,
             venue=("Vereinsheim Schachfreunde", "Paulanerplatz 1, 92224 Amberg", 49.4462, 11.8575),
             desc=p("7 Runden à 15 Minuten. Anmeldung vor Ort bis 12:30 Uhr.")),
        dict(org="tracht", cat="vereine", title="Probenabend Volkstanz",
             start=at(last_weekday(today, THU) - timedelta(weeks=1), "19:30"), dur_h=2,
             recurrence="weekly", venue=("Pfarrheim St. Martin", "Amberg", None, None),
             desc=p("Offene Probe – wer mittanzen will, kommt einfach vorbei.")),
        dict(org="redaktion", cat="maerkte-feste", title="Amberger Christkindlmarkt",
             start=at(today + timedelta(days=18), "11:00"),
             end=at(today + timedelta(days=45), "20:00"), featured=True, venue=v["marktplatz"],
             desc=p("Budenzauber vor dem gotischen Rathaus: Kunsthandwerk, Glühwein, "
                    "Lebkuchen und Musik auf der Bühne.")),
        dict(org="redaktion", cat="konzerte-party", title="Herbstkonzert der Stadtkapelle",
             start=at(today - timedelta(days=10), "19:00"), dur_h=2, venue=v["acc"],
             desc=p("Vergangene Veranstaltung – bleibt für Suchmaschinen erreichbar.")),
        dict(org="redaktion", cat="sonstiges", title="Lichterprozession zum Mariahilfberg",
             start=at(today + timedelta(days=30), "18:00"), dur_h=2, venue=v["mariahilfberg"],
             desc=p("Gemeinsamer Weg mit Kerzen hinauf zur Wallfahrtskirche.")),
        # Moderation demo data
        dict(org="cafe", cat="vereine", title="Spieleabend im Café", status="pending",
             start=at(today + timedelta(days=4), "19:00"), dur_h=3,
             venue=("Café am Vilsufer", "Schiffgasse 5, 92224 Amberg", 49.4435, 11.8556),
             desc=p("Brettspiele für alle – bringt eure Lieblingsspiele mit!")),
        dict(org="lauf", cat="sport", title="Flohmarkt", status="rejected",
             reason="Bitte Ort und genaue Uhrzeit ergänzen.",
             start=at(today + timedelta(days=8), "08:00"), dur_h=5, venue=(None, None, None, None),
             desc=p("Flohmarkt.")),
    ]


def build_offers(today: date) -> list[dict]:
    d = timedelta
    return [
        dict(org="cafe", title="2 Kaffee + 2 Stück Kuchen für 12 €", featured=True,
             valid_from=today, valid_until=today + d(days=30),
             desc=p("Jeden Nachmittag ab 14 Uhr. Gilt für alle hausgemachten Kuchen.")),
        dict(org="buch", title="10 % auf alle Kinderbücher",
             valid_from=today, valid_until=today + d(days=14),
             desc=p("Einfach an der Kasse „Amberg Live“ sagen.")),
        dict(org="gasthaus", title="Mittagstisch ab 9,90 €",
             valid_from=today - d(days=5), valid_until=None,
             desc=p("Dienstag bis Freitag, 11:30–14:00 Uhr. Wechselnde Gerichte.")),
        dict(org="wein", title="Glühwein-Probierpaket",
             valid_from=today + d(days=10), valid_until=today + d(days=40),
             desc=p("Drei Winzerglühweine für 19,90 € – perfekt für den Christkindlmarkt.")),
        dict(org="gasthaus", title="Herbst-Spezial: Schwammerl-Wochen",
             valid_from=today - d(days=40), valid_until=today - d(days=2),
             desc=p("Abgelaufenes Angebot (Demo).")),
        dict(org="cafe", title="Frühstück für zwei", status="pending",
             valid_from=today, valid_until=today + d(days=21),
             desc=p("Zwei Frühstücke nach Wahl + Prosecco für 29 €.")),
    ]
