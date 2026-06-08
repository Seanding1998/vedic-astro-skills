"""
vedic-calculator v0.4 - 完整原型
基于pysweph + dashaflow算法模块
输出完整的structured_data所需数据

v0.4: Dasha 计算接入 PyJHora（偏差 ≤2天），fallback 自建算法（6~9天）
v0.3: SAV/Shadbala fallback 显式 WARNING
"""
import swisseph as swe
from datetime import datetime, timedelta
import pytz
import json
import sys
import warnings

# dashaflow模块
from dashaflow.ashtakavarga import calculate_ashtakavarga
from dashaflow.dignity import get_dignity, get_compound_relationship, check_combustion, get_digbala
from dashaflow.jaimini import calculate_jaimini_karakas
try:
    from shadbala_pyjhora import calculate_shadbala_fixed as _shadbala_pyjhora
except ImportError:
    _shadbala_pyjhora = None
try:
    from ashtakavarga_pyjhora import calculate_ashtakavarga_fixed as _av_pyjhora
except ImportError:
    _av_pyjhora = None
    warnings.warn(
        "[vedic-calculator] ashtakavarga_pyjhora 未加载，SAV 将使用 dashaflow（精度较低）。"
        "请确保 vedic-calculator/scripts 目录在 sys.path 中，且 PyJHora 已正确安装。",
        RuntimeWarning, stacklevel=2
    )
try:
    from divisional_pyjhora import calculate_divisional_charts as _div_pyjhora
except ImportError:
    _div_pyjhora = None
try:
    from extras_pyjhora import (
        calculate_bhava_bala as _bhava_bala_pyjhora,
        calculate_special_lagnas as _special_lagnas_pyjhora,
        calculate_vargeeya_bala as _vargeeya_bala_pyjhora,
    )
except ImportError:
    _bhava_bala_pyjhora = None
    _special_lagnas_pyjhora = None
    _vargeeya_bala_pyjhora = None
try:
    from dasha_pyjhora import calculate_dasha_fixed as _dasha_pyjhora
except ImportError:
    _dasha_pyjhora = None

# === 配置 ===
swe.set_sid_mode(swe.SIDM_LAHIRI)

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_ABBR = ['Ar','Ta','Ge','Cn','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi']

PLANETS_SWE = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
    'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS, 'Saturn': swe.SATURN
}

SIGN_LORDS = {
    0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
    4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
    8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
}

NAKSHATRAS = [
    ('Ashwini','Ketu'), ('Bharani','Venus'), ('Krittika','Sun'),
    ('Rohini','Moon'), ('Mrigashira','Mars'), ('Ardra','Rahu'),
    ('Punarvasu','Jupiter'), ('Pushya','Saturn'), ('Ashlesha','Mercury'),
    ('Magha','Ketu'), ('Purva Phalguni','Venus'), ('Uttara Phalguni','Sun'),
    ('Hasta','Moon'), ('Chitra','Mars'), ('Swati','Rahu'),
    ('Vishakha','Jupiter'), ('Anuradha','Saturn'), ('Jyeshtha','Mercury'),
    ('Moola','Ketu'), ('Purva Ashadha','Venus'), ('Uttara Ashadha','Sun'),
    ('Shravana','Moon'), ('Dhanishta','Mars'), ('Shatabhisha','Rahu'),
    ('Purva Bhadrapada','Jupiter'), ('Uttara Bhadrapada','Saturn'), ('Revati','Mercury')
]

DASHA_ORDER = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
DASHA_YEARS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}

HOUSE_DOMAINS = {
    1:'自我', 2:'财富', 3:'兄弟', 4:'家庭', 5:'子女',
    6:'疾病', 7:'婚姻', 8:'变故', 9:'运势', 10:'事业',
    11:'收入', 12:'损耗'
}

# === 核心计算函数 ===

def to_jd(year, month, day, hour, minute, tz_str):
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime(year, month, day, hour, minute))
    utc_dt = local_dt.astimezone(pytz.utc)
    ut_hour = utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)

def calc_planet(jd, planet_id):
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd, planet_id, flags)
    lon = result[0][0]
    speed = result[0][3]
    sign_idx = int(lon / 30)
    degree = lon % 30
    deg_int = int(degree)
    min_int = round((degree - deg_int) * 60)
    return {
        'longitude': lon, 'sign': SIGNS[sign_idx], 'sign_idx': sign_idx,
        'degree': degree, 'deg_str': f"{deg_int}°{min_int:02d}'",
        'retrograde': speed < 0, 'speed': speed
    }

def calc_lagna(jd, lat, lon):
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    asc_lon = ascmc[0]
    sign_idx = int(asc_lon / 30)
    degree = asc_lon % 30
    deg_int = int(degree)
    min_int = round((degree - deg_int) * 60)
    return {
        'longitude': asc_lon, 'sign': SIGNS[sign_idx], 'sign_idx': sign_idx,
        'degree': degree, 'deg_str': f"{deg_int}°{min_int:02d}'"
    }

def get_nakshatra(longitude):
    nak_idx = int(longitude / (360/27))
    pada = int((longitude % (360/27)) / (360/108)) + 1
    name, lord = NAKSHATRAS[nak_idx]
    return {'name': name, 'pada': pada, 'lord': lord}

def get_house(planet_sign_idx, lagna_sign_idx):
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1

def calc_navamsha(longitude):
    """D9 Navamsha: each sign divided into 9 parts of 3°20'"""
    nav_part = int((longitude % 30) / (30/9))
    sign_idx = int(longitude / 30)
    # Navamsha starts from: Fire→Ar, Earth→Cp, Air→Li, Water→Cn
    element_start = [0, 9, 6, 3]  # Ar, Cp, Li, Cn
    element = sign_idx % 4  # 0=fire, 1=earth, 2=air, 3=water
    d9_sign_idx = (element_start[element] + nav_part) % 12
    return SIGNS[d9_sign_idx], d9_sign_idx

def calc_dashamsha(longitude):
    """D10 Dashamsha: each sign divided into 10 parts of 3°
    Odd signs: count from same sign
    Even signs: count from 9th sign (= +8 in 0-indexed)
    """
    part = int((longitude % 30) / 3)
    sign_idx = int(longitude / 30)
    if sign_idx % 2 == 0:  # Odd signs (Ar, Ge, Le...)
        d10_sign_idx = (sign_idx + part) % 12
    else:  # Even signs: 9th from sign = +8 (0-indexed)
        d10_sign_idx = (sign_idx + part + 8) % 12
    return SIGNS[d10_sign_idx], d10_sign_idx

def calc_chaturthamsha(longitude):
    """D4"""
    part = int((longitude % 30) / (30/4))
    sign_idx = int(longitude / 30)
    d4_sign_idx = (sign_idx + part * 3) % 12
    return SIGNS[d4_sign_idx], d4_sign_idx

def calc_panchamsha(longitude):
    """D5 Panchamsha: each sign divided into 5 parts of 6°
    BPHS lords:
      Odd signs:  Mars(Ar), Saturn(Aq), Jupiter(Sg), Mercury(Ge), Venus(Li)
      Even signs: Venus(Ta), Mercury(Vi), Jupiter(Pi), Saturn(Cp), Mars(Sc)
    """
    part = int((longitude % 30) / 6)
    sign_idx = int(longitude / 30)
    if sign_idx % 2 == 0:  # odd sign (0-indexed even = zodiac odd)
        starts = [0, 10, 8, 2, 6]    # Ar, Aq, Sg, Ge, Li
    else:  # even sign
        starts = [1, 5, 11, 9, 7]    # Ta, Vi, Pi, Cp, Sc
    d5_sign_idx = starts[part] if part < 5 else sign_idx
    return SIGNS[d5_sign_idx], d5_sign_idx

def calc_chara_karakas_7k8k(planets):
    """Calculate both 7K and 8K Chara Karakas"""
    # Effective degree = degree in sign (for Rahu: 30 - degree)
    karaka_data = []
    for name in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        karaka_data.append((name, planets[name]['degree']))
    
    # 7K: sort by degree descending, top 7
    sorted_7k = sorted(karaka_data, key=lambda x: x[1], reverse=True)
    karaka_names_7k = ['AK','AmK','BK','MK','PK','GK','DK']
    karakas_7k = [(karaka_names_7k[i], sorted_7k[i][0], sorted_7k[i][1]) 
                  for i in range(7)]
    
    # 8K: add Rahu (30 - degree)
    rahu_eff_deg = 30 - planets['Rahu']['degree']
    karaka_data_8k = karaka_data + [('Rahu', rahu_eff_deg)]
    sorted_8k = sorted(karaka_data_8k, key=lambda x: x[1], reverse=True)
    karaka_names_8k = ['AK','AmK','BK','MK','PiK','PK','GK','DK']
    karakas_8k = [(karaka_names_8k[i], sorted_8k[i][0], sorted_8k[i][1]) 
                  for i in range(8)]
    
    # DK争议: 比较7K的第7位 vs 8K的第7位
    # 目的：检测加入Rahu后，"第7位(配偶指示星位)"是否换了行星
    dk_7k = karakas_7k[6][1]  # 7K第7位
    dk_8k = sorted_8k[6][0]   # 8K第7位（不是第8位！）
    dk_consistent = dk_7k == dk_8k
    
    return {
        '7k': karakas_7k,
        '8k': karakas_8k,
        'dk_7k': dk_7k,
        'dk_8k': dk_8k,
        'dk_consistent': dk_consistent
    }

def calc_aspects(planets):
    """Calculate major aspects between planets"""
    aspects = []
    planet_names = list(planets.keys())
    for i in range(len(planet_names)):
        for j in range(i+1, len(planet_names)):
            p1, p2 = planet_names[i], planet_names[j]
            lon1, lon2 = planets[p1]['longitude'], planets[p2]['longitude']
            diff = abs(lon1 - lon2)
            if diff > 180: diff = 360 - diff
            
            # Check aspect types
            aspect_type = None
            orb = None
            if diff < 10:
                aspect_type = '合相'
                orb = diff
            elif abs(diff - 60) < 8:
                aspect_type = '六合(60°)'
                orb = abs(diff - 60)
            elif abs(diff - 90) < 8:
                aspect_type = '刑(90°)'
                orb = abs(diff - 90)
            elif abs(diff - 120) < 8:
                aspect_type = '三合(120°)'
                orb = abs(diff - 120)
            elif abs(diff - 180) < 10:
                aspect_type = '对冲(180°)'
                orb = abs(diff - 180)
            
            if aspect_type and orb is not None:
                aspects.append({
                    'p1': p1, 'p2': p2, 'type': aspect_type,
                    'degree_diff': round(diff, 2), 'orb': round(orb, 2)
                })
    
    # Sort by orb (tighter aspects first)
    aspects.sort(key=lambda x: x['orb'])
    return aspects[:8]  # Top 8 most significant

def calc_house_lords(lagna_sign_idx):
    """Calculate house lord table"""
    lords = {}
    for house in range(1, 13):
        sign_idx = (lagna_sign_idx + house - 1) % 12
        lord = SIGN_LORDS[sign_idx]
        lords[house] = {'sign': SIGNS[sign_idx], 'lord': lord, 'domain': HOUSE_DOMAINS[house]}
    return lords

def calc_vimsottari_dasha(moon_lon, birth_year, birth_month, birth_day, birth_hour, birth_minute):
    """Calculate Vimsottari Dasha periods"""
    nak = get_nakshatra(moon_lon)
    nak_lord = nak['lord']
    start_idx = DASHA_ORDER.index(nak_lord)
    
    nak_span = 360/27
    elapsed_in_nak = moon_lon % nak_span
    remaining_fraction = 1 - (elapsed_in_nak / nak_span)
    
    birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
    dashas = []
    # 第一个大运起始 = 出生日 - 已过大运年数（回溯到出生前）
    first_planet_years = DASHA_YEARS[DASHA_ORDER[start_idx]]
    elapsed_years = first_planet_years * (1 - remaining_fraction)
    current_dt = birth_dt - timedelta(days=elapsed_years * 365.25)
    
    for i in range(9):
        idx = (start_idx + i) % 9
        planet = DASHA_ORDER[idx]
        years = DASHA_YEARS[planet]
        days = years * 365.25
        end_dt = current_dt + timedelta(days=days)
        
        # Mark current
        now = datetime.now()
        is_current = current_dt <= now <= end_dt
        
        # Antardasha子期计算
        antardashas = []
        ad_start = current_dt
        for j in range(9):
            ad_idx = (idx + j) % 9
            ad_planet = DASHA_ORDER[ad_idx]
            ad_years = years * DASHA_YEARS[ad_planet] / 120
            ad_days = ad_years * 365.25
            ad_end = ad_start + timedelta(days=ad_days)
            ad_is_current = ad_start <= now <= ad_end
            antardashas.append({
                'planet': ad_planet,
                'start': ad_start.strftime('%Y-%m-%d'),
                'end': ad_end.strftime('%Y-%m-%d'),
                'is_current': ad_is_current
            })
            ad_start = ad_end
        
        dashas.append({
            'planet': planet,
            'start': current_dt.strftime('%Y-%m'),
            'end': end_dt.strftime('%Y-%m'),
            'years': round(years, 1),
            'is_current': is_current,
            'antardashas': antardashas
        })
        current_dt = end_dt
    
    return dashas

def calc_special_points(lagna, planets):
    """Calculate AL, UL and other special Jaimini points.
    Note: JHora may use different settings (Rahu/Ketu lord rules, dual-sign lords).
    Our implementation follows standard BPHS Jaimini method.
    """
    lagna_idx = lagna['sign_idx']
    
    def calc_arudha(house_num, lagna_idx):
        """Calculate Arudha Pada for a given house (BPHS standard)"""
        sign_idx = (lagna_idx + house_num - 1) % 12
        lord = SIGN_LORDS[sign_idx]
        lord_sign_idx = planets[lord]['sign_idx']
        # Count from house sign to lord (1-based: lord in same sign = 1st)
        dist = (lord_sign_idx - sign_idx) % 12
        # Arudha = same distance from lord's position
        arudha_idx = (lord_sign_idx + dist) % 12
        # BPHS Exception: arudha cannot be in 1st or 7th from house sign
        # If 1st → use 10th from house sign
        # If 7th → use 4th from house sign
        if arudha_idx == sign_idx:
            arudha_idx = (sign_idx + 9) % 12   # 10th from house sign
        elif arudha_idx == (sign_idx + 6) % 12:
            arudha_idx = (sign_idx + 3) % 12   # 4th from house sign
        return SIGNS[arudha_idx], arudha_idx
    
    al_sign, al_idx = calc_arudha(1, lagna_idx)
    al_house = get_house(al_idx, lagna_idx)
    
    ul_sign, ul_idx = calc_arudha(12, lagna_idx)
    ul_house = get_house(ul_idx, lagna_idx)
    
    return {
        'AL': {'sign': al_sign, 'sign_idx': al_idx, 'house': al_house},
        'UL': {'sign': ul_sign, 'sign_idx': ul_idx, 'house': ul_house},
    }

def calc_transits(lagna_sign_idx, moon_sign_idx):
    """Calculate current transit positions for slow planets.
    Used by core-pro for Sade Sati, BAV transit calibration, double transit.
    """
    now = datetime.now()
    jd_now = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    transits = {}
    # Slow planets: Saturn, Jupiter, Rahu, Ketu
    slow_planets = {'Saturn': swe.SATURN, 'Jupiter': swe.JUPITER}
    for name, pid in slow_planets.items():
        result = swe.calc_ut(jd_now, pid, flags)
        lon = result[0][0]
        sign_idx = int(lon / 30)
        house = get_house(sign_idx, lagna_sign_idx)
        transits[name] = {'sign': SIGNS[sign_idx], 'sign_idx': sign_idx, 'house': house}
    
    # Rahu (Mean Node)
    result = swe.calc_ut(jd_now, swe.MEAN_NODE, flags)
    rahu_lon = result[0][0]
    rahu_idx = int(rahu_lon / 30)
    transits['Rahu'] = {'sign': SIGNS[rahu_idx], 'sign_idx': rahu_idx, 
                        'house': get_house(rahu_idx, lagna_sign_idx)}
    ketu_idx = (rahu_idx + 6) % 12
    transits['Ketu'] = {'sign': SIGNS[ketu_idx], 'sign_idx': ketu_idx,
                        'house': get_house(ketu_idx, lagna_sign_idx)}
    
    # Sade Sati check
    saturn_idx = transits['Saturn']['sign_idx']
    sade_sati = 'inactive'
    if saturn_idx == (moon_sign_idx - 1) % 12:
        sade_sati = 'phase1_rising'
    elif saturn_idx == moon_sign_idx:
        sade_sati = 'phase2_peak'
    elif saturn_idx == (moon_sign_idx + 1) % 12:
        sade_sati = 'phase3_fading'
    transits['sade_sati'] = sade_sati
    
    # Double transit (Saturn-Jupiter intersection)
    sat_houses = {transits['Saturn']['house']}
    # Saturn aspects: 3rd, 7th, 10th
    sat_h = transits['Saturn']['house']
    for asp in [3, 7, 10]:
        sat_houses.add(((sat_h - 1 + asp - 1) % 12) + 1)
    
    jup_houses = {transits['Jupiter']['house']}
    # Jupiter aspects: 5th, 7th, 9th
    jup_h = transits['Jupiter']['house']
    for asp in [5, 7, 9]:
        jup_houses.add(((jup_h - 1 + asp - 1) % 12) + 1)
    
    double_transit = sorted(sat_houses & jup_houses)
    transits['double_transit_houses'] = double_transit
    transits['timestamp'] = now.strftime('%Y-%m-%d')
    
    return transits

# === 主计算函数 ===

def calculate_full_chart(year, month, day, hour, minute, lat, lon, tz_str="Asia/Kolkata"):
    """计算完整星盘数据"""
    jd = to_jd(year, month, day, hour, minute, tz_str)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    
    # 1. Lagna
    lagna = calc_lagna(jd, lat, lon)
    lagna['nakshatra'] = get_nakshatra(lagna['longitude'])
    lagna['house'] = 1
    
    # 2. Planets (7 main)
    planets = {}
    for name, pid in PLANETS_SWE.items():
        p = calc_planet(jd, pid)
        p['house'] = get_house(p['sign_idx'], lagna['sign_idx'])
        p['nakshatra'] = get_nakshatra(p['longitude'])
        planets[name] = p
    
    # 3. Rahu & Ketu
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    rahu_lon = result[0][0]
    rahu_sign_idx = int(rahu_lon / 30)
    rahu_deg = rahu_lon % 30
    planets['Rahu'] = {
        'longitude': rahu_lon, 'sign': SIGNS[rahu_sign_idx],
        'sign_idx': rahu_sign_idx, 'degree': rahu_deg,
        'deg_str': f"{int(rahu_deg)}°{round((rahu_deg%1)*60):02d}'",
        'retrograde': True, 'speed': result[0][3],
        'house': get_house(rahu_sign_idx, lagna['sign_idx']),
        'nakshatra': get_nakshatra(rahu_lon)
    }
    ketu_lon = (rahu_lon + 180) % 360
    ketu_sign_idx = int(ketu_lon / 30)
    ketu_deg = ketu_lon % 30
    planets['Ketu'] = {
        'longitude': ketu_lon, 'sign': SIGNS[ketu_sign_idx],
        'sign_idx': ketu_sign_idx, 'degree': ketu_deg,
        'deg_str': f"{int(ketu_deg)}°{round((ketu_deg%1)*60):02d}'",
        'retrograde': True, 'speed': -result[0][3],
        'house': get_house(ketu_sign_idx, lagna['sign_idx']),
        'nakshatra': get_nakshatra(ketu_lon)
    }
    
    # 4. SAV/BAV (via PyJHora, dashaflow fallback)
    ashtak = None
    if _av_pyjhora is not None:
        try:
            tz = pytz.timezone(tz_str)
            _tz_dt = tz.localize(datetime(year, month, day, hour, minute))
            _tz_offset = _tz_dt.utcoffset().total_seconds() / 3600.0
            ashtak = _av_pyjhora(year, month, day, hour, minute, lat, lon, _tz_offset)
        except Exception as e:
            ashtak = None
            print(f"⚠️ WARNING: PyJHora SAV 计算失败 ({e})，将使用 dashaflow fallback（精度较低）", file=sys.stderr)
    
    if ashtak is None:
        # Fallback to dashaflow — SAV 可能有 5/12 星座偏差！
        print("⚠️ WARNING: SAV 使用 dashaflow 计算（非 PyJHora）。结果可能与 JHora 有偏差！", file=sys.stderr)
        print("   修复方法: 运行 setup_env.py 或确保 PyJHora + scripts 目录在 sys.path 中", file=sys.stderr)
        from dashaflow.ashtakavarga import calculate_ashtakavarga
        planets_in_signs = {name: p['sign_idx'] for name, p in planets.items() if name not in ['Rahu','Ketu']}
        planets_in_signs['Rahu'] = planets['Rahu']['sign_idx']
        planets_in_signs['Ketu'] = planets['Ketu']['sign_idx']
        ashtak = calculate_ashtakavarga(planets_in_signs, lagna['sign_idx'])
    
    # Map SAV to houses
    sav_by_house = {}
    for h in range(1, 13):
        sign_idx = (lagna['sign_idx'] + h - 1) % 12
        sign_name = SIGNS[sign_idx]
        sav_by_house[h] = {'sign': sign_name, 'value': ashtak['sarvashtakavarga'].get(sign_name, 0)}
    
    # 5. Divisional charts (PyJHora: 15 charts, self-built fallback: 4 charts)
    divisional_charts = None
    if _div_pyjhora is not None:
        try:
            tz = pytz.timezone(tz_str)
            _tz_dt = tz.localize(datetime(year, month, day, hour, minute))
            _tz_offset = _tz_dt.utcoffset().total_seconds() / 3600.0
            divisional_charts = _div_pyjhora(
                year, month, day, hour, minute, lat, lon, _tz_offset
            )
        except Exception:
            divisional_charts = None
    
    if divisional_charts is not None:
        # Extract d9/d10/d4/d5 in legacy (sign_name, sign_idx) format for backward compat
        def _legacy_fmt(chart_key):
            ch = divisional_charts.get(chart_key, {})
            return {p: (ch[p]['sign'], ch[p]['sign_idx']) for p in ch if 'error' not in ch}
        d9 = _legacy_fmt('D9')
        d10 = _legacy_fmt('D10')
        d4 = _legacy_fmt('D4')
        d5 = _legacy_fmt('D5')
    else:
        # Fallback to self-built
        divisional_charts = {}
        d9, d10, d4, d5 = {}, {}, {}, {}
        for name, p in planets.items():
            d9[name] = calc_navamsha(p['longitude'])
            d10[name] = calc_dashamsha(p['longitude'])
            d4[name] = calc_chaturthamsha(p['longitude'])
            d5[name] = calc_panchamsha(p['longitude'])
        d9['Lagna'] = calc_navamsha(lagna['longitude'])
        d10['Lagna'] = calc_dashamsha(lagna['longitude'])
        d4['Lagna'] = calc_chaturthamsha(lagna['longitude'])
        d5['Lagna'] = calc_panchamsha(lagna['longitude'])
    
    # Vargottama check
    vargottama = {}
    for name in planets:
        d9_sign = d9.get(name, (None, None))
        d9_sign_name = d9_sign[0] if isinstance(d9_sign, tuple) else d9_sign.get('sign', None) if isinstance(d9_sign, dict) else None
        vargottama[name] = planets[name]['sign'] == d9_sign_name
    
    # 6. Dignity & Compound Relationship (自建，不依赖dashaflow)
    # BPHS Panchadha Maitri 算法
    
    # Step 1: 旺/入庙/陷检测
    EXALTATION = {'Sun':'Aries','Moon':'Taurus','Mars':'Capricorn',
                  'Mercury':'Virgo','Jupiter':'Cancer','Venus':'Pisces','Saturn':'Libra'}
    DEBILITATION = {'Sun':'Libra','Moon':'Scorpio','Mars':'Cancer',
                    'Mercury':'Pisces','Jupiter':'Capricorn','Venus':'Virgo','Saturn':'Aries'}
    OWN_SIGNS = {'Sun':['Leo'],'Moon':['Cancer'],'Mars':['Aries','Scorpio'],
                 'Mercury':['Gemini','Virgo'],'Jupiter':['Sagittarius','Pisces'],
                 'Venus':['Taurus','Libra'],'Saturn':['Capricorn','Aquarius']}
    
    # Step 2: 自然关系表 (Naisargika Maitri) - BPHS标准
    NATURAL_REL = {
        'Sun':     {'friend':['Moon','Mars','Jupiter'], 'enemy':['Venus','Saturn'], 'neutral':['Mercury']},
        'Moon':    {'friend':['Sun','Mercury'], 'enemy':[], 'neutral':['Mars','Jupiter','Venus','Saturn']},
        'Mars':    {'friend':['Sun','Moon','Jupiter'], 'enemy':['Mercury'], 'neutral':['Venus','Saturn']},
        'Mercury': {'friend':['Sun','Venus'], 'enemy':['Moon'], 'neutral':['Mars','Jupiter','Saturn']},
        'Jupiter': {'friend':['Sun','Moon','Mars'], 'enemy':['Mercury','Venus'], 'neutral':['Saturn']},
        'Venus':   {'friend':['Mercury','Saturn'], 'enemy':['Sun','Moon'], 'neutral':['Mars','Jupiter']},
        'Saturn':  {'friend':['Mercury','Venus'], 'enemy':['Sun','Moon','Mars'], 'neutral':['Jupiter']},
    }
    
    def get_natural_rel(planet, lord):
        """查自然关系: friend/enemy/neutral"""
        if planet == lord:
            return 'own'
        rel = NATURAL_REL.get(planet, {})
        if lord in rel.get('friend', []): return 'friend'
        if lord in rel.get('enemy', []): return 'enemy'
        return 'neutral'
    
    def get_temporal_rel(planet_sign_idx, lord_sign_idx):
        """查临时关系: 座主落在行星的2/3/4/10/11/12宫=临时友"""
        dist = (lord_sign_idx - planet_sign_idx) % 12
        # 距离2,3,4,10,11,12宫 = dist值1,2,3,9,10,11 (0-indexed)
        return 'temp_friend' if dist in {1,2,3,9,10,11} else 'temp_enemy'
    
    # Step 4: Panchadha合成表
    COMPOUND_TABLE = {
        ('friend', 'temp_friend'):   'great_friend',
        ('friend', 'temp_enemy'):    'neutral',
        ('enemy',  'temp_friend'):   'neutral',
        ('enemy',  'temp_enemy'):    'great_enemy',
        ('neutral','temp_friend'):   'friend',
        ('neutral','temp_enemy'):    'enemy',
    }
    
    dignity_data = {}
    for name in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        p = planets[name]
        sign = p['sign']
        lord = SIGN_LORDS[p['sign_idx']]
        
        # Step 1: 旺/入庙/陷直接确定
        if EXALTATION.get(name) == sign:
            compound = 'exalted'
        elif DEBILITATION.get(name) == sign:
            compound = 'debilitated'
        elif sign in OWN_SIGNS.get(name, []):
            compound = 'own_sign'
        else:
            # Step 2+3+4: 自然+临时→合成
            natural = get_natural_rel(name, lord)
            if natural == 'own':
                compound = 'own_sign'
            else:
                # 找座主的实际位置
                lord_sign_idx = planets[lord]['sign_idx'] if lord in planets else p['sign_idx']
                temporal = get_temporal_rel(p['sign_idx'], lord_sign_idx)
                compound = COMPOUND_TABLE.get((natural, temporal), 'neutral')
        
        dignity_data[name] = {'basic': compound, 'compound': compound}
    
    # 7. Combustion check
    sun_lon = planets['Sun']['longitude']
    combustion = {}
    for name in ['Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        is_retro = planets[name]['retrograde']
        comb_result = check_combustion(name, planets[name]['longitude'], sun_lon, is_retro)
        is_combust = comb_result if isinstance(comb_result, bool) else comb_result.get('is_combust', False)
        if is_combust:
            diff = abs(planets[name]['longitude'] - sun_lon)
            if diff > 180: diff = 360 - diff
            combustion[name] = {'distance': round(diff, 2)}
    
    # 8. Chara Karakas
    karakas = calc_chara_karakas_7k8k(planets)
    
    # 9. Aspects
    aspects = calc_aspects(planets)
    
    # 10. House lords
    house_lords = calc_house_lords(lagna['sign_idx'])
    # Add planet positions to house lords
    for h, info in house_lords.items():
        planet = info['lord']
        if planet in planets:
            info['lord_house'] = planets[planet]['house']
    
    # 11. Vimsottari Dasha (PyJHora preferred, self-built fallback)
    dashas = None
    if _dasha_pyjhora is not None:
        try:
            tz = pytz.timezone(tz_str)
            _tz_dt = tz.localize(datetime(year, month, day, hour, minute))
            _tz_off = _tz_dt.utcoffset().total_seconds() / 3600
            dashas = _dasha_pyjhora(year, month, day, hour, minute, lat, lon, _tz_off)
        except Exception as e:
            print(f"⚠️ PyJHora Dasha failed ({e}), using self-built fallback", file=sys.stderr)
    if dashas is None:
        dashas = calc_vimsottari_dasha(planets['Moon']['longitude'], year, month, day, hour, minute)
    
    # 12. Shadbala (via PyJHora fixed wrapper, dashaflow fallback)
    shadbala_data = None
    if _shadbala_pyjhora is not None:
        try:
            # Compute tz_offset from tz_str
            tz = pytz.timezone(tz_str)
            _tz_dt = tz.localize(datetime(year, month, day, hour, minute))
            _tz_offset = _tz_dt.utcoffset().total_seconds() / 3600.0
            shadbala_data = _shadbala_pyjhora(
                year, month, day, hour, minute, lat, lon, _tz_offset
            )
        except Exception as e:
            shadbala_data = {'error': f'PyJHora: {e}'}
    
    if shadbala_data is None:
        # Fallback to dashaflow
        try:
            from dashaflow.shadbala import calculate_shadbala
            planets_data_for_sb = {}
            raw_planets_for_sb = {}
            for name in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
                p = planets[name]
                planets_data_for_sb[name] = {
                    'sign': p['sign'], 'sign_idx': p['sign_idx'],
                    'degree': p['degree'], 'house': p['house'],
                    'dignity': dignity_data[name]['basic'],
                    'is_retrograde': p['retrograde']
                }
                raw_planets_for_sb[name] = {
                    'lon': p['longitude'], 'sign_idx': p['sign_idx'],
                    'speed': p['speed']
                }
            is_day = 6 <= hour <= 18
            shadbala_data = calculate_shadbala(planets_data_for_sb, raw_planets_for_sb, is_day)
        except Exception as e:
            shadbala_data = {'error': str(e)}
    
    # 13. Moon phase
    moon_sun_diff = (planets['Moon']['longitude'] - planets['Sun']['longitude']) % 360
    is_waxing = moon_sun_diff < 180
    
    # 14. Digbala
    digbala = {}
    for name in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        digbala[name] = get_digbala(name, planets[name]['house'])
    
    # 15. Special Points (AL, UL)
    special_points = calc_special_points(lagna, planets)
    
    # 16. Transit positions (current slow planet positions)
    transits = calc_transits(lagna['sign_idx'], planets['Moon']['sign_idx'])
    
    # 17. Bhava Bala, Special Lagnas, Vargeeya Bala (via PyJHora)
    bhava_bala = None
    special_lagnas = None
    vargeeya_bala = None
    if any([_bhava_bala_pyjhora, _special_lagnas_pyjhora, _vargeeya_bala_pyjhora]):
        try:
            tz = pytz.timezone(tz_str)
            _tz_dt = tz.localize(datetime(year, month, day, hour, minute))
            _tz_offset = _tz_dt.utcoffset().total_seconds() / 3600.0
            if _bhava_bala_pyjhora:
                bhava_bala = _bhava_bala_pyjhora(year, month, day, hour, minute, lat, lon, _tz_offset)
            if _special_lagnas_pyjhora:
                special_lagnas = _special_lagnas_pyjhora(year, month, day, hour, minute, lat, lon, _tz_offset)
            if _vargeeya_bala_pyjhora:
                vargeeya_bala = _vargeeya_bala_pyjhora(year, month, day, hour, minute, lat, lon, _tz_offset)
        except Exception:
            pass
    
    return {
        'ayanamsa': ayanamsa,
        'lagna': lagna,
        'planets': planets,
        'sav': ashtak['sarvashtakavarga'],
        'sav_by_house': sav_by_house,
        'bav': ashtak['bhinnashtakavarga'],
        'd9': d9, 'd10': d10, 'd4': d4, 'd5': d5,
        'divisional_charts': divisional_charts,
        'vargottama': vargottama,
        'dignity': dignity_data,
        'combustion': combustion,
        'karakas': karakas,
        'aspects': aspects,
        'house_lords': house_lords,
        'dashas': dashas,
        'shadbala': shadbala_data,
        'moon_phase': {'waxing': is_waxing, 'sun_moon_diff': round(moon_sun_diff, 1)},
        'digbala': digbala,
        'special_points': special_points,
        'transits': transits,
        'bhava_bala': bhava_bala,
        'special_lagnas': special_lagnas,
        'vargeeya_bala': vargeeya_bala,
    }


# === TEST ===
if __name__ == '__main__':
    print("=== vedic-calculator v0.2 Full Test ===\n")
    
    # Gandhi: 1869-10-02, 07:12, Porbandar
    chart = calculate_full_chart(1869, 10, 2, 7, 12, 21.6417, 69.6293, "Asia/Kolkata")
    
    print(f"Ayanamsa (Lahiri): {chart['ayanamsa']:.4f}°")
    print(f"Lagna: {chart['lagna']['sign']} {chart['lagna']['deg_str']}")
    
    print(f"\n--- Planets ---")
    print(f"  {'Planet':<10} {'Sign':<12} {'Deg':>8} {'H':>3} {'R':>2} {'Dignity':<16} {'Compound'}")
    for name in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
        p = chart['planets'][name]
        r = 'R' if p['retrograde'] else ''
        dig = chart['dignity'].get(name, {})
        basic = dig.get('basic', '-')
        compound = dig.get('compound', '-')
        print(f"  {name:<10} {p['sign']:<12} {p['deg_str']:>8} {p['house']:>3} {r:>2} {str(basic):<16} {compound}")
    
    print(f"\n--- SAV by House ---")
    total = 0
    for h in range(1, 13):
        s = chart['sav_by_house'][h]
        total += s['value']
        print(f"  {h}宫({s['sign'][:2]}): {s['value']}", end='  ')
        if h % 6 == 0: print()
    print(f"  Total: {total}")
    
    print(f"\n--- Chara Karakas (7K) ---")
    for k, planet, deg in chart['karakas']['7k']:
        print(f"  {k}: {planet} ({deg:.1f}°)")
    print(f"  DK争议: 7K={chart['karakas']['dk_7k']}, 8K={chart['karakas']['dk_8k']}, 一致={chart['karakas']['dk_consistent']}")
    
    print(f"\n--- Aspects (top 5) ---")
    for a in chart['aspects'][:5]:
        print(f"  {a['p1']}-{a['p2']}: {a['type']} ({a['degree_diff']}°, orb {a['orb']}°)")
    
    print(f"\n--- Dasha ---")
    for d in chart['dashas']:
        marker = '→' if d['is_current'] else ' '
        print(f"  {marker} {d['planet']:<10} {d['start']} ~ {d['end']}  ({d['years']}yr)")
    
    print(f"\n--- D9 Navamsha ---")
    for name in ['Lagna','Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
        sign = chart['d9'][name][0]
        varg = ' ★V' if chart['vargottama'].get(name, False) else ''
        print(f"  {name:<10} → {sign}{varg}")
    
    print(f"\n--- Shadbala ---")
    if 'error' in chart['shadbala']:
        print(f"  Error: {chart['shadbala']['error']}")
    else:
        for name, data in chart['shadbala'].items():
            if isinstance(data, dict):
                total = data.get('total_rupas', data.get('total', '?'))
                print(f"  {name:<10} {total}")
    
    print(f"\n--- Moon Phase ---")
    phase = chart['moon_phase']
    print(f"  {'盈月(Shukla)' if phase['waxing'] else '亏月(Krishna)'}, 距Sun {phase['sun_moon_diff']}°")
    
    print(f"\n--- Combustion ---")
    if chart['combustion']:
        for name, data in chart['combustion'].items():
            print(f"  {name}: {data}")
    else:
        print("  无燃烧行星")
    
    print(f"\n--- House Lords ---")
    for h in range(1, 13):
        info = chart['house_lords'][h]
        print(f"  {h}宫({info['domain']}): {info['lord']} → {info.get('lord_house','?')}宫")
    
    print(f"\n✅ 全部14个数据板块计算完成!")
