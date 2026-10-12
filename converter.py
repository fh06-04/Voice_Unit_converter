"""Natural-language unit conversion.

Parses spoken or typed requests such as "convert twenty five kilometers to miles"
and performs the conversion. No eval() is used anywhere, so arbitrary input is safe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


class ConversionError(ValueError):
    """Raised with a user-friendly message when a request can't be converted."""


@dataclass(frozen=True)
class Unit:
    category: str
    singular: str
    plural: str
    factor: float | None  # multiplier to the category's base unit (None = temperature)


# category, singular, plural, factor to base unit, extra aliases
_DEFS = [
    # length (base: meter)
    ("length", "meter", "meters", 1.0, ["metre", "metres", "m"]),
    ("length", "kilometer", "kilometers", 1000.0, ["kilometre", "kilometres", "km", "kms"]),
    ("length", "centimeter", "centimeters", 0.01, ["centimetre", "centimetres", "cm"]),
    ("length", "millimeter", "millimeters", 0.001, ["millimetre", "millimetres", "mm"]),
    ("length", "mile", "miles", 1609.344, ["mi"]),
    ("length", "yard", "yards", 0.9144, ["yd", "yds"]),
    ("length", "foot", "feet", 0.3048, ["ft", "foots"]),
    ("length", "inch", "inches", 0.0254, []),
    # mass (base: kilogram)
    ("mass", "kilogram", "kilograms", 1.0, ["kilo", "kilos", "kg", "kgs", "kilogramme"]),
    ("mass", "gram", "grams", 0.001, ["g", "gm", "gms", "gramme"]),
    ("mass", "milligram", "milligrams", 1e-6, ["mg"]),
    ("mass", "pound", "pounds", 0.45359237, ["lb", "lbs"]),
    ("mass", "ounce", "ounces", 0.028349523125, ["oz"]),
    ("mass", "stone", "stone", 6.35029318, ["stones"]),
    ("mass", "tonne", "tonnes", 1000.0, ["metric ton", "metric tons", "ton", "tons"]),
    # volume (base: liter, US customary)
    ("volume", "liter", "liters", 1.0, ["litre", "litres", "l"]),
    ("volume", "milliliter", "milliliters", 0.001, ["millilitre", "millilitres", "ml"]),
    ("volume", "gallon", "gallons", 3.785411784, ["gal"]),
    ("volume", "quart", "quarts", 0.946352946, ["qt"]),
    ("volume", "pint", "pints", 0.473176473, ["pt"]),
    ("volume", "cup", "cups", 0.2365882365, []),
    ("volume", "fluid ounce", "fluid ounces", 0.0295735295625, ["fl oz", "floz"]),
    ("volume", "tablespoon", "tablespoons", 0.01478676478125, ["tbsp"]),
    ("volume", "teaspoon", "teaspoons", 0.00492892159375, ["tsp"]),
    # temperature (special handling)
    ("temperature", "degree Celsius", "degrees Celsius", None, ["celsius", "centigrade", "c"]),
    ("temperature", "degree Fahrenheit", "degrees Fahrenheit", None, ["fahrenheit", "f"]),
    ("temperature", "kelvin", "kelvin", None, ["kelvins", "k"]),
    # speed (base: meter per second)
    ("speed", "meter per second", "meters per second", 1.0,
     ["metre per second", "metres per second", "mps", "m/s"]),
    ("speed", "kilometer per hour", "kilometers per hour", 1 / 3.6,
     ["kilometre per hour", "kilometres per hour", "kph", "kmh", "kmph", "km/h"]),
    ("speed", "mile per hour", "miles per hour", 0.44704, ["mph", "mi/h"]),
    ("speed", "knot", "knots", 1852 / 3600, ["kn", "kt"]),
    # time (base: second)
    ("time", "second", "seconds", 1.0, ["sec", "secs", "s"]),
    ("time", "minute", "minutes", 60.0, ["min", "mins"]),
    ("time", "hour", "hours", 3600.0, ["hr", "hrs", "h"]),
    ("time", "day", "days", 86400.0, ["d"]),
    ("time", "week", "weeks", 604800.0, ["wk", "wks"]),
    ("time", "year", "years", 31536000.0, ["yr", "yrs"]),
    # digital storage (base: byte, decimal prefixes)
    ("data", "byte", "bytes", 1.0, ["b"]),
    ("data", "kilobyte", "kilobytes", 1e3, ["kb"]),
    ("data", "megabyte", "megabytes", 1e6, ["mb"]),
    ("data", "gigabyte", "gigabytes", 1e9, ["gb"]),
    ("data", "terabyte", "terabytes", 1e12, ["tb"]),
]

_ALIASES: dict[str, Unit] = {}
_CATEGORIES: dict[str, list[str]] = {}
for _cat, _sing, _plur, _factor, _extra in _DEFS:
    _unit = Unit(_cat, _sing, _plur, _factor)
    _CATEGORIES.setdefault(_cat, []).append(_sing)
    for _name in {_sing.lower(), _plur.lower(), *[a.lower() for a in _extra]}:
        _ALIASES.setdefault(_name, _unit)


def list_units() -> dict[str, list[str]]:
    """Units grouped by category (used by the manual-entry form in the UI)."""
    return {cat: list(names) for cat, names in _CATEGORIES.items()}


# --------------------------------------------------------------------------- numbers
_SMALL = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: (i + 2) * 10 for i, w in enumerate(
    "twenty thirty forty fifty sixty seventy eighty ninety".split())}
_SCALES = {"thousand": 1e3, "million": 1e6, "billion": 1e9}
_NUM_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)$")


def parse_number(tokens: list[str]) -> tuple[float, int] | None:
    """Read a number (digits or words) from the start of ``tokens``.

    Returns ``(value, tokens_consumed)`` or ``None`` if there is no number.
    """
    i, sign = 0, 1
    if tokens and tokens[0] in ("minus", "negative"):
        sign, i = -1, 1
    total = current = 0.0
    seen = False
    while i < len(tokens):
        t = tokens[i]
        if t in ("a", "an") and not seen and i + 1 < len(tokens) \
                and (tokens[i + 1] in _SCALES or tokens[i + 1] == "hundred"):
            current, seen = 1.0, True
        elif t in _SMALL:
            current += _SMALL[t]; seen = True
        elif t in _TENS:
            current += _TENS[t]; seen = True
        elif t == "hundred" and seen:
            current = (current or 1) * 100
        elif t in _SCALES and seen:
            total += (current or 1) * _SCALES[t]; current = 0.0
        elif _NUM_RE.match(t):
            if seen:
                break
            current, seen = float(t), True
        elif t == "and" and seen and i + 1 < len(tokens) \
                and (tokens[i + 1] in _SMALL or tokens[i + 1] in _TENS):
            pass
        elif t == "point":
            digits, j = "", i + 1
            while j < len(tokens):
                d = tokens[j]
                if d in _SMALL and _SMALL[d] < 10:
                    digits += str(_SMALL[d])
                elif d.isdigit() and len(d) == 1:
                    digits += d
                else:
                    break
                j += 1
            if not digits:
                break
            return sign * (total + current + float("0." + digits)), j
        else:
            break
        i += 1
    if not seen:
        return None
    return sign * (total + current), i


# --------------------------------------------------------------------------- parsing
_PREFIXES = [
    "please", "can you", "could you", "hey", "okay", "ok", "what is", "what are",
    "whats", "how much is", "how much are", "tell me", "convert", "change", "turn",
    "calculate", "give me",
]
_SUFFIXES = (" please", " thanks", " thank you")
_CONNECTOR = re.compile(r"\s+(?:equal to|equals|into|to|in|as)\s+")
_HOW_MANY = re.compile(
    r"^how many (?P<to>.+?)\s+(?:(?:are|is)\s+)?(?:there\s+)?in\s+(?P<src>.+)$")

HINT = "Try something like: “convert 5 kilometers to miles”."


def normalize(text: str) -> str:
    t = text.lower().replace("’", "").replace("'", "").replace("°", " ")
    t = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", t)        # twenty-five -> twenty five
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)           # 1,000 -> 1000
    t = re.sub(r"[^a-z0-9./\-\s]", " ", t)
    t = re.sub(r"(?<=\d)(?=[a-z])", " ", t)             # 5km -> 5 km
    return re.sub(r"\s+", " ", t).strip()


def _strip_fillers(t: str) -> str:
    changed = True
    while changed:
        changed = False
        for p in _PREFIXES:
            if t.startswith(p + " "):
                t, changed = t[len(p) + 1:], True
        for s in _SUFFIXES:
            if t.endswith(s):
                t, changed = t[: -len(s)], True
    return t.strip()


def lookup_unit(raw: str) -> Unit:
    s = re.sub(r"^(?:degrees?|the|a|an)\s+", "", raw.strip())
    candidates = [s]
    if s.endswith("es"):
        candidates.append(s[:-2])
    if s.endswith("s"):
        candidates.append(s[:-1])
    for c in candidates:
        if c in _ALIASES:
            return _ALIASES[c]
    raise ConversionError(f"I don't know the unit “{raw}”.")


def _parse_quantity(part: str, default_one: bool = False) -> tuple[float, str]:
    tokens = part.split()
    if not tokens:
        raise ConversionError(f"I didn't catch what to convert. {HINT}")
    parsed = parse_number(tokens)
    if parsed:
        value, used = parsed
        tokens = tokens[used:]
    elif tokens[0] in ("a", "an", "the") or default_one:
        value = 1.0
        tokens = tokens[1:] if tokens[0] in ("a", "an", "the") else tokens
    else:
        raise ConversionError(f"I couldn't find a number in “{part}”. {HINT}")
    if not tokens:
        raise ConversionError("I heard a number but no unit.")
    return value, " ".join(tokens)


# --------------------------------------------------------------------------- converting
def _temp_kind(unit: Unit) -> str:
    n = unit.singular.lower()
    return "c" if "celsius" in n else "f" if "fahrenheit" in n else "k"


def _convert_value(value: float, a: Unit, b: Unit) -> float:
    if a.category != "temperature":
        return value * a.factor / b.factor  # type: ignore[operator]
    ka, kb = _temp_kind(a), _temp_kind(b)
    celsius = value if ka == "c" else (value - 32) * 5 / 9 if ka == "f" else value - 273.15
    if celsius < -273.15 - 1e-9:
        raise ConversionError("That temperature is below absolute zero.")
    return celsius if kb == "c" else celsius * 9 / 5 + 32 if kb == "f" else celsius + 273.15


def format_number(x: float) -> str:
    if x == 0:
        return "0"
    if abs(x) >= 1e15 or abs(x) < 1e-6:
        return f"{x:.6g}"
    return f"{float(f'{x:.8g}'):.10f}".rstrip("0").rstrip(".")


def _name(unit: Unit, value: float) -> str:
    return unit.singular if abs(value) == 1 else unit.plural


@dataclass(frozen=True)
class Conversion:
    value: float
    result: float
    from_unit: Unit
    to_unit: Unit

    def to_dict(self) -> dict:
        fn, tn = _name(self.from_unit, self.value), _name(self.to_unit, self.result)
        v, r = format_number(self.value), format_number(self.result)
        return {
            "value": self.value,
            "result": self.result,
            "from_unit": fn,
            "to_unit": tn,
            "category": self.from_unit.category,
            "display": f"{v} {fn} = {r} {tn}",
            "spoken": f"{v} {fn} is {r} {tn}",
        }


def convert_text(text: str) -> Conversion:
    """Parse a natural-language request and return the conversion."""
    t = _strip_fillers(normalize(text))
    if not t:
        raise ConversionError(f"I didn't catch anything. {HINT}")

    m = _HOW_MANY.match(t)
    if m:
        value, src = _parse_quantity(m["src"], default_one=True)
        dest = m["to"]
    else:
        parts = _CONNECTOR.split(t, maxsplit=1)
        if len(parts) < 2:
            raise ConversionError(f"I couldn't tell what to convert to. {HINT}")
        value, src = _parse_quantity(parts[0])
        dest = parts[1]

    a, b = lookup_unit(src), lookup_unit(dest)
    if a.category != b.category:
        raise ConversionError(f"Can't convert {a.category} to {b.category}.")
    return Conversion(value, _convert_value(value, a, b), a, b)
