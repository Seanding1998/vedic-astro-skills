#!/usr/bin/env python3
"""Clean-room native Vedic chart calculator for vedic-astro-skills.

This script adds a direct birth-data calculation path without reusing another
repository's implementation. It preserves the existing JHora markdown/PDF path:
use this script when birth date, local clock time, coordinates, and an IANA
timezone are available; use jhora_markdown_bridge.py + chart_sanity_check.py
when a JHora export is available.

Implemented in this first native layer:
- Swiss Ephemeris sidereal D1 positions for Lagna and 9 grahas.
- Whole-sign house mapping from Lagna.
- Nakshatra and pada derived from absolute longitude.
- Mean-node Rahu and derived Ketu at exact opposition.
- House lords, Chara Karakas, Parashari graha drishti, AL/UL.
- Optional PyJHora adapter for SAV/BAV and D9/D10/D4/D5.

Not implemented here on purpose:
- CNWU16's corrected Shadbala implementation. Keep Shadbala sourced from JHora
  exports until a separate formula-level clean-room implementation is written.
- Full MD/AD/PD Vimsottari. Do not use this script for month/day-level dasha
  timing until a separately tested dasha module is added.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import swisseph as swe
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: install pysweph to use scripts/vedic_native_calculator.py") from exc

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

PLANET_BODIES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}
PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PYJHORA_PLANET_IDS = {
    "0": "Sun", "1": "Moon", "2": "Mars", "3": "Mercury", "4": "Jupiter",
    "5": "Venus", "6": "Saturn", "7": "Rahu", "8": "Ketu",
    "L": "Lagna", "Asc": "Lagna", "Ascendant": "Lagna", "Lagna": "Lagna",
}
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]
BAV_ROW_CONSTANTS = {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56, "Venus": 52, "Saturn": 39}
EXALTATION = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"}
DEBILITATION = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}
OWN_SIGNS = {
    "Sun": {"Leo"}, "Moon": {"Cancer"}, "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"}, "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"}, "Saturn": {"Capricorn", "Aquarius"},
}
HOUSE_DOMAINS = {
    1: "self", 2: "resources", 3: "effort", 4: "home", 5: "creativity", 6: "conflict",
    7: "relationship", 8: "transformation", 9: "fortune", 10: "career", 11: "gains", 12: "loss_release",
}


@dataclass(frozen=True)
class BirthInput:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float
    tz: str
    place: str = "birth_place"
    time_precision: str = "exact_to_minute"
    time_source: str = "unspecified"
    gender: str = ""
    relationship: str = ""


def sign_index(longitude: float) -> int:
    return int((longitude % 360.0) // 30.0)


def degree_in_sign(longitude: float) -> float:
    return longitude % 30.0


def degree_label(degree: float) -> str:
    whole = int(degree)
    minutes = int(round((degree - whole) * 60.0))
    if minutes == 60:
        whole += 1
        minutes = 0
    return f"{whole:02d}deg{minutes:02d}'"


def house_from_lagna(body_sign_idx: int, lagna_sign_idx: int) -> int:
    return ((body_sign_idx - lagna_sign_idx) % 12) + 1


def unwrap_swe_position(result: Any) -> tuple[float, float]:
    values = result[0] if isinstance(result, tuple) and result and isinstance(result[0], (tuple, list)) else result
    if not isinstance(values, (tuple, list)) or len(values) < 4:
        raise RuntimeError(f"Unexpected swisseph result shape: {result!r}")
    return float(values[0]) % 360.0, float(values[3])


def configure_swe() -> str:
    mode = "TRUE_CITRA"
    sidm = getattr(swe, "SIDM_TRUE_CITRA", None)
    if sidm is None:
        sidm = getattr(swe, "SIDM_LAHIRI", None)
        mode = "LAHIRI_FALLBACK"
    if sidm is not None:
        swe.set_sid_mode(sidm)
    ephe_dir = Path(__file__).resolve().parent / "ephe"
    if ephe_dir.exists():
        swe.set_ephe_path(str(ephe_dir))
    return mode


def local_datetime_and_offset(birth: BirthInput) -> tuple[datetime, float, bool | None]:
    naive = datetime(birth.year, birth.month, birth.day, birth.hour, birth.minute)
    try:
        import pytz
    except ImportError:
        pytz = None
    if pytz is not None:
        zone = pytz.timezone(birth.tz)
        aware = zone.localize(naive, is_dst=None)
    else:
        try:
            from zoneinfo import ZoneInfo
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install pytz on Python versions without zoneinfo support") from exc
        aware = naive.replace(tzinfo=ZoneInfo(birth.tz))
    offset = aware.utcoffset()
    dst = aware.dst()
    return aware, (offset.total_seconds() / 3600.0 if offset else 0.0), bool(dst and dst.total_seconds())


def julian_day_ut(local_dt: datetime) -> float:
    utc = local_dt.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0
    return float(swe.julday(utc.year, utc.month, utc.day, hour))


def julian_day_local(birth: BirthInput) -> float:
    return float(swe.julday(birth.year, birth.month, birth.day, birth.hour + birth.minute / 60.0))


def nakshatra_for(longitude: float) -> dict[str, Any]:
    nak_size = 360.0 / 27.0
    pada_size = nak_size / 4.0
    idx = int((longitude % 360.0) // nak_size)
    pada = int(((longitude % 360.0) % nak_size) // pada_size) + 1
    name, lord = NAKSHATRAS[idx]
    return {"name": name, "pada": pada, "lord": lord}


def calc_lagna(jd_ut: float, lat: float, lon: float) -> dict[str, Any]:
    flags = getattr(swe, "FLG_SIDEREAL", 0)
    try:
        houses, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", flags)
    except TypeError:
        houses, ascmc = swe.houses_ex(jd_ut, lat, lon, flags, b"W")
    _ = houses
    longitude = float(ascmc[0]) % 360.0
    idx = sign_index(longitude)
    degree = degree_in_sign(longitude)
    return {
        "sign": SIGNS[idx], "sign_idx": idx, "degree": degree,
        "deg_str": degree_label(degree), "longitude": longitude,
        "nakshatra": nakshatra_for(longitude),
    }


def planet_entry(name: str, longitude: float, speed: float, lagna_sign_idx: int) -> dict[str, Any]:
    idx = sign_index(longitude)
    degree = degree_in_sign(longitude)
    retrograde = speed < 0.0 or name in {"Rahu", "Ketu"}
    return {
        "sign": SIGNS[idx], "sign_idx": idx, "degree": degree,
        "deg_str": degree_label(degree), "longitude": longitude % 360.0,
        "house": house_from_lagna(idx, lagna_sign_idx), "retrograde": retrograde,
        "speed": speed,
        "nakshatra": nakshatra_for(longitude)["name"],
        "pada": nakshatra_for(longitude)["pada"],
        "nakshatra_lord": nakshatra_for(longitude)["lord"],
    }


def calc_planets(jd_ut: float, lagna_sign_idx: int) -> dict[str, dict[str, Any]]:
    flags = getattr(swe, "FLG_SWIEPH", 0) | getattr(swe, "FLG_SIDEREAL", 0) | getattr(swe, "FLG_SPEED", 0)
    planets: dict[str, dict[str, Any]] = {}
    for name, body in PLANET_BODIES.items():
        longitude, speed = unwrap_swe_position(swe.calc_ut(jd_ut, body, flags))
        planets[name] = planet_entry(name, longitude, speed, lagna_sign_idx)
    rahu_lon, rahu_speed = unwrap_swe_position(swe.calc_ut(jd_ut, swe.MEAN_NODE, flags))
    planets["Rahu"] = planet_entry("Rahu", rahu_lon, rahu_speed, lagna_sign_idx)
    planets["Ketu"] = planet_entry("Ketu", rahu_lon + 180.0, rahu_speed, lagna_sign_idx)
    return planets


def calc_house_lords(lagna_sign_idx: int, planets: dict[str, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for house in range(1, 13):
        idx = (lagna_sign_idx + house - 1) % 12
        sign = SIGNS[idx]
        lord = SIGN_LORDS[sign]
        result[house] = {
            "sign": sign, "lord": lord, "domain": HOUSE_DOMAINS[house],
            "lord_house": planets.get(lord, {}).get("house"),
        }
    return result


def calc_dignity(planets: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for planet in PLANET_ORDER[:7]:
        sign = planets[planet]["sign"]
        if sign == EXALTATION[planet]:
            dignity = "exalted"
        elif sign == DEBILITATION[planet]:
            dignity = "debilitated"
        elif sign in OWN_SIGNS[planet]:
            dignity = "own"
        else:
            dignity = "ordinary"
        result[planet] = {"basic": dignity, "dispositor": SIGN_LORDS[sign]}
    return result


def calc_chara_karakas(planets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels_7k = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
    labels_8k = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
    seven = sorted(((name, planets[name]["degree"]) for name in PLANET_ORDER[:7]), key=lambda item: item[1], reverse=True)
    eight = sorted([*seven, ("Rahu", 30.0 - planets["Rahu"]["degree"])], key=lambda item: item[1], reverse=True)
    rows_7k = [(label, planet, round(deg, 4)) for label, (planet, deg) in zip(labels_7k, seven)]
    rows_8k = [(label, planet, round(deg, 4)) for label, (planet, deg) in zip(labels_8k, eight)]
    return {"7k": rows_7k, "8k": rows_8k, "dk_7k": rows_7k[-1][1], "dk_8k": rows_8k[-1][1]}


def calc_graha_drishti(planets: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    offsets = {
        "Sun": [7], "Moon": [7], "Mars": [4, 7, 8], "Mercury": [7],
        "Jupiter": [5, 7, 9], "Venus": [7], "Saturn": [3, 7, 10], "Rahu": [7], "Ketu": [7],
    }
    result: dict[str, dict[str, Any]] = {}
    for planet, entry in planets.items():
        source_house = int(entry["house"])
        houses = [((source_house + offset - 2) % 12) + 1 for offset in offsets[planet]]
        hits = [name for name, other in planets.items() if name != planet and other["house"] in houses]
        result[planet] = {
            "from_house": source_house, "aspected_houses": houses,
            "aspected_planets": hits, "amplify": planet == "Rahu",
        }
    return result


def calc_special_points(house_lords: dict[int, dict[str, Any]], lagna_sign_idx: int) -> dict[str, dict[str, Any]]:
    def arudha(base_house: int) -> dict[str, Any] | None:
        lord_house = house_lords[base_house].get("lord_house")
        if not lord_house:
            return None
        base_idx = (lagna_sign_idx + base_house - 1) % 12
        lord_idx = (lagna_sign_idx + int(lord_house) - 1) % 12
        distance = (lord_idx - base_idx) % 12
        arudha_idx = (lord_idx + distance) % 12
        if arudha_idx in {base_idx, (base_idx + 6) % 12}:
            arudha_idx = (lord_idx + 9) % 12
        return {"sign": SIGNS[arudha_idx], "house": house_from_lagna(arudha_idx, lagna_sign_idx)}

    result: dict[str, dict[str, Any]] = {}
    al = arudha(1)
    ul = arudha(12)
    if al:
        result["AL"] = al
    if ul:
        result["UL"] = ul
    return result


def patch_swe_for_pyjhora() -> None:
    for attr in ("calc_ut", "calc"):
        original = getattr(swe, attr, None)
        if original is None or getattr(original, "_seanding_shape_patch", False):
            continue

        def wrapper(jd: float, planet: int, flags: int = 0, _original=original):
            result = _original(jd, planet, flags)
            return (result[0], result[1]) if isinstance(result, tuple) and len(result) == 3 else result

        wrapper._seanding_shape_patch = True  # type: ignore[attr-defined]
        setattr(swe, attr, wrapper)

    original_houses = getattr(swe, "houses_ex", None)
    if original_houses is not None and not getattr(original_houses, "_seanding_shape_patch", False):

        def houses_wrapper(*args: Any, **kwargs: Any):
            result = original_houses(*args, **kwargs)
            return (result[0], result[1]) if isinstance(result, tuple) and len(result) == 3 else result

        houses_wrapper._seanding_shape_patch = True  # type: ignore[attr-defined]
        swe.houses_ex = houses_wrapper


def configure_pyjhora() -> tuple[Any, Any, Any]:
    # pysweph>=2.10 returns the two-item result shape PyJHora 4.8.6 expects.
    # Do not mutate swisseph globals here: this calculator also uses them for D1.
    import jhora
    from jhora import const
    from jhora.horoscope.chart import ashtakavarga, charts
    from jhora import utils
    from jhora.panchanga import drik
    from jhora.panchanga.drik import Date, Place

    ephe_dir = Path(jhora.__file__).resolve().parent / "data" / "ephe"
    if ephe_dir.exists():
        swe.set_ephe_path(str(ephe_dir))
    try:
        drik.set_ayanamsa_mode("TRUE_CITRA")
    except Exception:
        pass
    if hasattr(const, "_DEFAULT_AYANAMSA_MODE"):
        const._DEFAULT_AYANAMSA_MODE = "TRUE_CITRA"
    if hasattr(const, "_use_true_nodes_for_rahu_ketu"):
        const._use_true_nodes_for_rahu_ketu = False
    return Date, Place, charts, ashtakavarga, utils


def pyjhora_julian_day(birth: BirthInput, Date: Any, utils: Any) -> float:
    """Build the JD through PyJHora's public Date/time API, not a private conversion."""
    return float(
        utils.julian_day_number(
            Date(birth.year, birth.month, birth.day),
            (birth.hour, birth.minute, 0),
        )
    )


def pyjhora_ashtakavarga(birth: BirthInput, tz_offset: float) -> dict[str, Any]:
    Date, Place, charts, ashtakavarga, utils = configure_pyjhora()
    place = Place(birth.place or "birth_place", birth.lat, birth.lon, tz_offset)
    rasi = charts.rasi_chart(pyjhora_julian_day(birth, Date, utils), place)
    h2p_slots: list[list[str]] = [[] for _ in range(12)]
    for item in rasi:
        if not isinstance(item, (tuple, list)) or len(item) < 2:
            continue
        pos = item[1]
        if not isinstance(pos, (tuple, list)) or not pos:
            continue
        sign = int(pos[0])
        if 0 <= sign < 12:
            h2p_slots[sign].append(str(item[0]))
    h2p = ["/".join(slot) for slot in h2p_slots]
    bav_raw, sav_raw, _prastara = ashtakavarga.get_ashtaka_varga(h2p)
    sav = {sign: int(round(float(sav_raw[idx]))) for idx, sign in enumerate(SIGNS)}
    bav: dict[str, dict[str, int]] = {}
    for row_idx, planet in enumerate(BAV_ROW_CONSTANTS):
        row = bav_raw[row_idx]
        bav[planet] = {sign: int(round(float(row[idx]))) for idx, sign in enumerate(SIGNS)}
    return {"sarvashtakavarga": sav, "bhinnashtakavarga": bav, "sav_total": sum(sav.values()), "source": "PyJHora"}


def normalize_pyjhora_body_id(raw: Any) -> str | None:
    key = str(raw).strip()
    if key in PYJHORA_PLANET_IDS:
        return PYJHORA_PLANET_IDS[key]
    if key.startswith("L"):
        return "Lagna"
    return None


def pyjhora_divisional_charts(birth: BirthInput, tz_offset: float, factors: tuple[int, ...] = (9, 10, 4, 5)) -> dict[str, Any]:
    Date, Place, charts, _ashtakavarga, utils = configure_pyjhora()
    place = Place(birth.place or "birth_place", birth.lat, birth.lon, tz_offset)
    jd = pyjhora_julian_day(birth, Date, utils)
    result: dict[str, Any] = {}
    for factor in factors:
        rows = charts.divisional_chart(jd, place, divisional_chart_factor=factor, chart_method=1)
        chart: dict[str, Any] = {}
        for item in rows:
            if not isinstance(item, (tuple, list)) or len(item) < 2:
                continue
            body = normalize_pyjhora_body_id(item[0])
            pos = item[1]
            if body is None or not isinstance(pos, (tuple, list)) or not pos:
                continue
            idx = int(pos[0])
            if 0 <= idx < 12:
                chart[body] = {"sign": SIGNS[idx], "sign_idx": idx}
        result[f"D{factor}"] = chart
    return result


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    planets = payload.get("planets", {})
    checks["planet_count"] = {"ok": all(name in planets for name in PLANET_ORDER), "count": len(planets)}
    if "Rahu" in planets and "Ketu" in planets:
        diff = abs(float(planets["Rahu"]["longitude"]) - float(planets["Ketu"]["longitude"])) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        checks["rahu_ketu_180"] = {"ok": math.isclose(diff, 180.0, abs_tol=0.01), "diff": round(diff, 6)}
    sav = payload.get("sav") or {}
    bav = payload.get("bav") or {}
    if sav:
        total = sum(float(sav.get(sign, 0.0)) for sign in SIGNS)
        checks["sav_total"] = {"ok": math.isclose(total, 337.0, abs_tol=0.01), "total": total}
    if bav:
        rows: dict[str, Any] = {}
        for planet, expected in BAV_ROW_CONSTANTS.items():
            row = bav.get(planet, {})
            actual = sum(float(row.get(sign, 0.0)) for sign in SIGNS)
            rows[planet] = {"ok": math.isclose(actual, expected, abs_tol=0.01), "total": actual, "expected": expected}
        checks["bav_row_constants"] = rows
        if sav:
            cols: dict[str, Any] = {}
            for sign in SIGNS:
                actual = sum(float((bav.get(planet) or {}).get(sign, 0.0)) for planet in BAV_ROW_CONSTANTS)
                expected = float(sav.get(sign, 0.0))
                cols[sign] = {"ok": math.isclose(actual, expected, abs_tol=0.01), "total": actual, "expected": expected}
            checks["bav_to_sav_columns"] = cols
    return checks


def calculate_chart(birth: BirthInput, *, require_ashtakavarga: bool = False) -> dict[str, Any]:
    ayanamsa_mode = configure_swe()
    local_dt, tz_offset, is_dst = local_datetime_and_offset(birth)
    jd_ut = julian_day_ut(local_dt)
    ayanamsa = float(swe.get_ayanamsa_ut(jd_ut))
    lagna = calc_lagna(jd_ut, birth.lat, birth.lon)
    planets = calc_planets(jd_ut, int(lagna["sign_idx"]))
    house_lords = calc_house_lords(int(lagna["sign_idx"]), planets)

    ashtakavarga_status: dict[str, Any] = {"ok": False, "source": None, "error": None}
    sav: dict[str, int] = {}
    bav: dict[str, dict[str, int]] = {}
    try:
        av = pyjhora_ashtakavarga(birth, tz_offset)
        sav = av["sarvashtakavarga"]
        bav = av["bhinnashtakavarga"]
        ashtakavarga_status = {"ok": True, "source": av.get("source"), "error": None}
    except Exception as exc:
        ashtakavarga_status["error"] = f"{type(exc).__name__}: {exc}"
        if require_ashtakavarga:
            raise RuntimeError(f"Ashtakavarga calculation failed: {ashtakavarga_status['error']}") from exc

    divisional_status: dict[str, Any] = {"ok": False, "error": None}
    divisional_charts: dict[str, Any] = {}
    try:
        divisional_charts = pyjhora_divisional_charts(birth, tz_offset)
        divisional_status["ok"] = bool(divisional_charts)
    except Exception as exc:
        divisional_status["error"] = f"{type(exc).__name__}: {exc}"

    sav_by_house = {
        house: {
            "sign": SIGNS[(int(lagna["sign_idx"]) + house - 1) % 12],
            "value": sav.get(SIGNS[(int(lagna["sign_idx"]) + house - 1) % 12]),
        }
        for house in range(1, 13)
    }
    payload: dict[str, Any] = {
        "metadata": {
            "calculator": "seanding-clean-room-native",
            "birth_date": f"{birth.year:04d}-{birth.month:02d}-{birth.day:02d}",
            "birth_time": f"{birth.hour:02d}:{birth.minute:02d}",
            "place": birth.place,
            "lat": birth.lat,
            "lon": birth.lon,
            "timezone": birth.tz,
            "utc_offset_hours": tz_offset,
            "is_dst": is_dst,
            "time_precision": birth.time_precision,
            "time_source": birth.time_source,
            "gender": birth.gender,
            "relationship": birth.relationship,
            "ayanamsa_mode": ayanamsa_mode,
            "node_mode": "Mean Node",
            "limitations": [
                "No native Shadbala correction layer in this script.",
                "No full MD/AD/PD Vimsottari dasha layer in this script.",
            ],
        },
        "ayanamsa": ayanamsa,
        "lagna": lagna,
        "planets": planets,
        "house_lords": house_lords,
        "karakas": calc_chara_karakas(planets),
        "dignity": calc_dignity(planets),
        "graha_drishti": calc_graha_drishti(planets),
        "special_points": calc_special_points(house_lords, int(lagna["sign_idx"])),
        "sav": sav,
        "sav_by_house": sav_by_house,
        "bav": bav,
        "ashtakavarga_status": ashtakavarga_status,
        "divisional_charts": divisional_charts,
        "divisional_status": divisional_status,
    }
    payload["validation"] = validate_payload(payload)
    return payload


def markdown_table(header: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return lines


def format_markdown(chart: dict[str, Any]) -> str:
    meta = chart["metadata"]
    lines: list[str] = []
    lines.append("## 元信息")
    lines.append("```")
    lines.append(f"出生: {meta['birth_date']} {meta['birth_time']} {meta['timezone']}")
    lines.append(f"地点: {meta['place']} ({meta['lon']}, {meta['lat']})")
    lines.append(f"Ayanamsa: {chart['ayanamsa']:.6f} ({meta['ayanamsa_mode']})")
    lines.append(f"Node模式: {meta['node_mode']}")
    lines.append(f"计算器: {meta['calculator']}")
    lines.append("```")
    lines.append("")

    rows = [["Lagna", chart["lagna"]["sign"], 1, chart["lagna"]["deg_str"], "-"]]
    for planet in PLANET_ORDER:
        p = chart["planets"][planet]
        rows.append([planet, p["sign"], p["house"], p["deg_str"], "R" if p["retrograde"] else "D"])
    lines.append("## D1基础数据")
    lines.extend(markdown_table(["Body", "Sign", "House", "Degree", "Motion"], rows))
    lines.append("")

    nak_rows = [["Lagna", chart["lagna"]["nakshatra"]["name"], chart["lagna"]["nakshatra"]["pada"], chart["lagna"]["nakshatra"]["lord"]]]
    for planet in PLANET_ORDER:
        p = chart["planets"][planet]
        nak_rows.append([planet, p["nakshatra"], p["pada"], p["nakshatra_lord"]])
    lines.append("## Nakshatra")
    lines.extend(markdown_table(["Body", "Nakshatra", "Pada", "Lord"], nak_rows))
    lines.append("")

    if chart.get("sav"):
        lines.append("## SAV")
        lines.extend(markdown_table([*SIGN_ABBR, "Total"], [[*(chart["sav"].get(sign, "") for sign in SIGNS), sum(chart["sav"].values())]]))
        lines.append("")
    else:
        lines.append("## SAV")
        lines.append(f"SAV/BAV未取得：{chart['ashtakavarga_status'].get('error')}")
        lines.append("")

    if chart.get("bav"):
        lines.append("## BAV")
        bav_rows = []
        for planet in BAV_ROW_CONSTANTS:
            row = chart["bav"].get(planet, {})
            values = [row.get(sign, "") for sign in SIGNS]
            bav_rows.append([planet, *values, sum(int(v) for v in values if v != "")])
        lines.extend(markdown_table(["Planet", *SIGN_ABBR, "Row"], bav_rows))
        lines.append("")

    lines.append("## 宫主表")
    house_rows = []
    for house in range(1, 13):
        h = chart["house_lords"][house]
        house_rows.append([house, h["sign"], h["lord"], h["lord_house"], h["domain"]])
    lines.extend(markdown_table(["House", "Sign", "Lord", "Lord House", "Domain"], house_rows))
    lines.append("")

    if chart.get("divisional_charts"):
        lines.append("## 分盘数据")
        for key, dchart in chart["divisional_charts"].items():
            lines.append(f"### {key}")
            rows = []
            for body in ["Lagna", *PLANET_ORDER]:
                if body in dchart:
                    rows.append([body, dchart[body]["sign"]])
            lines.extend(markdown_table(["Body", "Sign"], rows))
            lines.append("")

    lines.append("## 校验结果")
    lines.append("```json")
    lines.append(json.dumps(chart["validation"], ensure_ascii=False, indent=2, sort_keys=True))
    lines.append("```")
    return "\n".join(lines) + "\n"


def parse_birth_args(args: argparse.Namespace) -> BirthInput:
    try:
        year, month, day = [int(part) for part in args.date.split("-")]
        hour, minute = [int(part) for part in args.time.split(":")]
    except ValueError as exc:
        raise SystemExit("--date must be YYYY-MM-DD and --time must be HH:MM") from exc
    return BirthInput(
        year=year, month=month, day=day, hour=hour, minute=minute,
        lat=float(args.lat), lon=float(args.lon), tz=args.tz, place=args.place,
        time_precision=args.time_precision, time_source=args.time_source,
        gender=args.gender, relationship=args.relationship,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean-room native Vedic chart calculator")
    parser.add_argument("--date", required=True, help="Birth date, YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="Birth local clock time, HH:MM")
    parser.add_argument("--lat", required=True, type=float, help="Birth latitude")
    parser.add_argument("--lon", required=True, type=float, help="Birth longitude")
    parser.add_argument("--tz", required=True, help="IANA timezone, e.g. Asia/Shanghai")
    parser.add_argument("--place", default="birth_place")
    parser.add_argument("--gender", default="")
    parser.add_argument("--relationship", default="")
    parser.add_argument("--time-precision", default="exact_to_minute")
    parser.add_argument("--time-source", default="unspecified")
    parser.add_argument("--output", default="structured_data_native.md", help="Markdown output path")
    parser.add_argument("--json-output", default="structured_data_native.json", help="JSON output path")
    parser.add_argument("--require-ashtakavarga", action="store_true", help="Fail if PyJHora SAV/BAV cannot be calculated")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    chart = calculate_chart(parse_birth_args(args), require_ashtakavarga=args.require_ashtakavarga)
    Path(args.output).write_text(format_markdown(chart), encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(chart, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {args.output}")
    if args.json_output:
        print(f"Wrote {args.json_output}")
    sav_check = chart["validation"].get("sav_total")
    if sav_check:
        print(f"SAV total: {sav_check['total']} ok={sav_check['ok']}")
    else:
        print(f"Ashtakavarga unavailable: {chart['ashtakavarga_status'].get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
