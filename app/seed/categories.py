"""Default categories. Slugs are fixed so URLs like /events?kategorie=sport never change."""

CATEGORIES = [
    # name,               slug,            icon,      color
    ("Konzerte & Party",  "konzerte-party", "music",   "#db2777"),
    ("Familie & Kinder",  "familie-kinder", "family",  "#16a34a"),
    ("Sport",             "sport",          "sport",   "#2563eb"),
    ("Essen & Trinken",   "essen-trinken",  "food",    "#ea580c"),
    ("Kultur & Museen",   "kultur-museen",  "culture", "#7c3aed"),
    ("Märkte & Feste",    "maerkte-feste",  "market",  "#ca8a04"),
    ("Vereine",           "vereine",        "club",    "#0d9488"),
    ("Sonstiges",         "sonstiges",      "other",   "#64748b"),
]
