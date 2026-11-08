"""Default categories. Slugs are fixed so URLs like /events?kategorie=sport never change.

Colours are one family: similar lightness and muted saturation, so no category shouts
and all sit calmly next to the honey-gold accent (text on them is never required).
"""

CATEGORIES = [
    # name,               slug,            icon,      color
    ("Konzerte & Party",  "konzerte-party", "music",   "#b34d6d"),  # berry
    ("Familie & Kinder",  "familie-kinder", "family",  "#5e8c4f"),  # meadow
    ("Sport",             "sport",          "sport",   "#3f7aa3"),  # Vils blue
    ("Essen & Trinken",   "essen-trinken",  "food",    "#c0683d"),  # paprika
    ("Kultur & Museen",   "kultur-museen",  "culture", "#7a5ea3"),  # plum
    ("Märkte & Feste",    "maerkte-feste",  "market",  "#b98a2e"),  # ochre
    ("Vereine",           "vereine",        "club",    "#33807a"),  # teal
    ("Sonstiges",         "sonstiges",      "other",   "#7b746a"),  # warm slate
]
