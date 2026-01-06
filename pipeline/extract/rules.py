import re
from typing import Optional, Tuple

# Keyword lists for classification
ACTION_KEYWORDS = [
    r"\bevacuate",
    r"\bcurfew",
    r"\bshelter (open|opening|closed|closing)",
    r"\bsuspend(ed)?",
    r"\bresume",
    r"\bclosure",
    r"\bclosed\b",
    r"\bdetour",
    r"\bdo not travel",
    r"\bseek shelter",
    r"\brelocate",
]

CATEGORY_KEYWORDS = [
    ("shelter", [r"shelter", r"evacuation center", r"general population"]),
    ("medical", [r"hospital", r"clinic", r"medical", r"ems", r"oxygen", r"dialysis", r"pharmacy"]),
    ("food-water", [r"water distribution", r"potable", r"boil water", r"food", r"meals", r"ice", r"supplies"]),
    ("utilities", [r"power", r"outage", r"generator", r"utility", r"water service", r"sewer", r"internet"]),
    ("transportation", [r"road", r"bridge", r"causeway", r"transit", r"bus", r"rail", r"airport", r"port", r"ferry"]),
]

URGENCY_HIGH = [
    r"\bevacuate",
    r"\bmandatory",
    r"\bimmediately",
    r"\blife[- ]threatening",
    r"\bcurfew",
    r"\bdo not travel",
    r"\bshelter in place",
]
URGENCY_MEDIUM = [
    r"\bstrongly encouraged",
    r"\bexpected",
    r"\bpossible",
    r"\bwatch\b",
    r"\badvisory",
    r"\blimited service",
    r"\bpartial",
    r"\bdelays",
]

ACTION_TYPE_PATTERNS = [
    ("Shelter Open", [r"shelter (open|opening)"] ),
    ("Shelter Closing", [r"shelter (closed|closing|demobiliz)"] ),
    ("Evacuation Order/Lift", [r"evacuation (order|lift|mandatory|voluntary)"] ),
    ("Curfew", [r"\bcurfew"] ),
    ("Road Closure/Detour", [r"road closed", r"bridge closed", r"detour"] ),
    ("Transit Suspension/Resumption", [r"transit", r"bus", r"rail", r"service (suspend|resume)"] ),
    ("Power Outage/Restoration", [r"power outage", r"restoration", r"crews working"] ),
    ("Water Advisory", [r"boil water", r"water distribution", r"water advisory"] ),
    ("Medical Support", [r"medical shelter", r"oxygen", r"dialysis", r"special needs"] ),
    ("Supply Distribution", [r"distribution", r"food", r"water", r"ice", r"supplies"] ),
]

BROWARD_CITIES = [
    "fort lauderdale",
    "plantation",
    "pompano",
    "coral springs",
    "hollywood",
    "broward",
]

MIAMI_DADE_CITIES = [
    "miami",
    "miami beach",
    "hialeah",
    "doral",
    "homestead",
    "coral gables",
    "miami-dade",
    "miami dade",
]


def detect_mode(text: str) -> str:
    lowered = text.lower()
    for pattern in ACTION_KEYWORDS:
        if re.search(pattern, lowered):
            return "action"
    return "info"


def detect_category(text: str) -> Optional[str]:
    lowered = text.lower()
    for category, patterns in CATEGORY_KEYWORDS:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return category
    return None


def detect_urgency(text: str) -> str:
    lowered = text.lower()
    for pattern in URGENCY_HIGH:
        if re.search(pattern, lowered):
            return "high"
    for pattern in URGENCY_MEDIUM:
        if re.search(pattern, lowered):
            return "medium"
    return "low"


def detect_action_type(text: str) -> Optional[str]:
    lowered = text.lower()
    for label, patterns in ACTION_TYPE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return label
    return None


def infer_location(text: str, source: str) -> Tuple[Optional[str], Optional[str]]:
    lowered = text.lower()
    county = None
    city = None

    if "broward" in source.lower():
        county = "broward"
    if "miami" in source.lower():
        county = "miami-dade"

    for c in BROWARD_CITIES:
        if c in lowered:
            county = "broward"
            city = c.title()
            break
    if county is None:
        for c in MIAMI_DADE_CITIES:
            if c in lowered:
                county = "miami-dade"
                city = c.title()
                break

    return county, city
