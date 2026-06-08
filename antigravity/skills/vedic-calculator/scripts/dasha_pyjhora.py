"""
dasha_pyjhora.py — PyJHora Vimsottari Dasha 包装器
使用 PyJHora 的精确天文算法计算大运/小运日期，偏差 ≤ 2 天（vs JHora PDF）。
自建 engine.py 的 365.25 近似法偏差 6~9 天。

返回格式与 engine.py 的 calc_vimsottari_dasha() 完全兼容。
"""

import swisseph as swe
import os
import sys
from datetime import datetime


# Planet ID ↔ Name mapping (PyJHora convention: RAHU=7, KETU=8)
_PLANET_NAMES = {
    0: 'Sun', 1: 'Moon', 2: 'Mars', 3: 'Mercury',
    4: 'Jupiter', 5: 'Venus', 6: 'Saturn', 7: 'Rahu', 8: 'Ketu'
}

# Standard Vimsottari Dasha durations
_DASHA_YEARS = {
    'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
    'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17
}

# Standard Vimsottari Antardasha order: from dasha lord, cycle through 9 planets
_DASHA_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']


def _setup_jhora():
    """Apply the same monkey-patches as ashtakavarga_pyjhora.py"""
    # Patch swe.calc_ut for pysweph 2.10+ compatibility
    orig_calc = swe.calc_ut
    if not getattr(orig_calc, '_dasha_patched', False):
        def patched_calc(jd, planet, flags=0):
            r = orig_calc(jd, planet, flags=flags)
            return r[0], r[1] if len(r) > 1 else 0
        patched_calc._dasha_patched = True
        swe.calc_ut = patched_calc

    # Patch swe.houses_ex
    if hasattr(swe, 'houses_ex'):
        orig_he = swe.houses_ex
        if not getattr(orig_he, '_dasha_patched', False):
            def patched_he(*a, **kw):
                r = orig_he(*a, **kw)
                return (r[0], r[1]) if len(r) == 3 else r
            patched_he._dasha_patched = True
            swe.houses_ex = patched_he


def calculate_dasha_fixed(year, month, day, hour, minute, lat, lon, tz_offset):
    """Calculate Vimsottari Dasha using PyJHora's precise algorithm.
    
    Args:
        year, month, day: Birth date
        hour, minute: Birth time (local)
        lat, lon: Birth coordinates
        tz_offset: Timezone offset in hours (e.g., 8.0 for Asia/Shanghai)
    
    Returns:
        List of dasha dicts compatible with engine.py format:
        [{'planet': str, 'start': 'YYYY-MM', 'end': 'YYYY-MM', 'years': float,
          'is_current': bool, 'antardashas': [...]}, ...]
    """
    _setup_jhora()

    # Set ephemeris path
    from jhora.panchanga import drik
    ephe_dir = os.path.join(
        os.path.dirname(os.path.dirname(drik.__file__)), 'data', 'ephe'
    )
    if os.path.isdir(ephe_dir):
        swe.set_ephe_path(ephe_dir)

    # Configure ayanamsa (same as ashtakavarga_pyjhora)
    from jhora import const
    from jhora.panchanga.drik import Place
    from jhora.horoscope.dhasa.graha import vimsottari

    drik.set_ayanamsa_mode('TRUE_CITRA')
    const._DEFAULT_AYANAMSA_MODE = 'TRUE_CITRA'
    const._use_true_nodes_for_rahu_ketu = False

    # Create Place and JD (local time, same as ashtakavarga)
    place = Place('birth_place', lat, lon, tz_offset)
    local_hour = hour + minute / 60.0
    jd_local = swe.julday(year, month, day, local_hour)

    # ── 1. Get Mahadasha start dates ──
    md_dict = vimsottari.vimsottari_mahadasa(jd_local, place)
    # md_dict: OrderedDict {planet_id: start_jd}

    # ── 2. Get Antardasha entries ──
    try:
        result = vimsottari.get_vimsottari_dhasa_bhukthi(
            jd_local, place, dhasa_level_index=2  # ANTARA level
        )
        _, ad_entries = result[0], result[1]
    except Exception:
        ad_entries = []

    # Build antardasha lookup: {md_planet_id: [(ad_planet_name, start_date_str, end_date_str), ...]}
    ad_lookup = {}
    for i, entry in enumerate(ad_entries):
        md_id, ad_id = entry[0]
        y, m, d, h = entry[1]
        ad_start = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        ad_planet = _PLANET_NAMES.get(ad_id, f'P{ad_id}')

        if md_id not in ad_lookup:
            ad_lookup[md_id] = []
        ad_lookup[md_id].append((ad_planet, ad_start))

    # ── 3. Build output ──
    now = datetime.now()
    md_items = list(md_dict.items())
    dashas = []

    for i, (pid, start_jd) in enumerate(md_items):
        planet = _PLANET_NAMES.get(pid, f'P{pid}')
        years = _DASHA_YEARS.get(planet, 0)

        # Start date
        sy, sm, sd, sh = swe.revjul(start_jd)
        start_dt = datetime(int(sy), int(sm), int(sd))
        start_str = start_dt.strftime('%Y-%m')

        # End date = next dasha's start, or start + years
        if i + 1 < len(md_items):
            next_jd = list(md_dict.values())[i + 1]
            ey, em, ed, eh = swe.revjul(next_jd)
            end_dt = datetime(int(ey), int(em), int(ed))
        else:
            # Last dasha: estimate end
            from dateutil.relativedelta import relativedelta
            end_dt = start_dt + relativedelta(years=years)
        end_str = end_dt.strftime('%Y-%m')

        is_current = start_dt <= now <= end_dt

        # Build antardashas
        antardashas = []
        ad_list = ad_lookup.get(pid, [])
        for j, (ad_planet, ad_start_str) in enumerate(ad_list):
            # End = next antardasha's start
            if j + 1 < len(ad_list):
                ad_end_str = ad_list[j + 1][1]
            else:
                ad_end_str = end_dt.strftime('%Y-%m-%d')

            ad_start_dt = datetime.strptime(ad_start_str, '%Y-%m-%d')
            ad_end_dt = datetime.strptime(ad_end_str, '%Y-%m-%d')
            ad_is_current = ad_start_dt <= now <= ad_end_dt

            antardashas.append({
                'planet': ad_planet,
                'start': ad_start_str,
                'end': ad_end_str,
                'is_current': ad_is_current,
            })

        dashas.append({
            'planet': planet,
            'start': start_str,
            'end': end_str,
            'years': round(years, 1),
            'is_current': is_current,
            'antardashas': antardashas,
        })

    return dashas
